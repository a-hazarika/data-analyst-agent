"""
validate(sql) takes the SQL the model wrote and either returns a safe version
of it or raises UnsafeSql. Nothing the model writes reaches the database
without passing through here first.

It never looks at the SQL as text. Text checks ("does it contain DELETE?")
are easy to fool with comments, odd spacing or a column called deleted_at.
Instead sqlglot parses the SQL into a tree of nodes, and every rule below is
a question about that tree.
"""

from pathlib import Path
from typing import Final

import sqlglot
import yaml
from sqlglot import exp # exp holds the node types: exp.Select, exp.Table, exp.Func, ...
from sqlglot.errors import SqlglotError

# The views the model may read, straight from the catalog.
# frozenset stops the contents from being changed, but someone can still point the name at a new object
# Annotating with Final allows a type checker to flag that reassignment
VIEW_NAMES: Final = frozenset(yaml.safe_load(Path("catalog.yaml").read_text(encoding="utf-8"))["views"])

# The most rows any query may return.
MAX_ROWS = 200

# Functions the model may call. Anything not listed is refused, so a function
# nobody thought about (pg_sleep, set_config, pg_read_file, dblink ...) is
# blocked by default. When a good question is refused because of a harmless
# function, add its name here.
#
# The names are sqlglot's, in lower case. For most functions that is the
# Postgres name. A few differ, because sqlglot uses one name across all
# databases; the Postgres spelling is in the comment beside each.
ALLOWED_FUNCTIONS: Final = frozenset({
    # totals
    "count", "sum", "avg", "min", "max", "stddev", "median",
    "group_concat",      # string_agg
    "array_agg",
    "logical_or",        # bool_or
    "logical_and",       # bool_and
    "percentile_cont", "percentile_disc", "mode",
    # ranking and neighbours (used with OVER)
    "row_number", "rank", "dense_rank", "lag", "lead", "ntile",
    "first_value", "last_value",
    # numbers
    "round", "floor", "ceil", "abs", "greatest", "least",
    # text
    "lower", "upper", "initcap", "length", "trim", "concat", "replace",
    "substring", "left", "right", "split_part",
    "str_position",      # position('a' in x)
    # dates
    "timestamp_trunc",   # date_trunc('month', ...) on a timestamp
    "date_trunc",        # date_trunc on a date
    "extract",           # extract(year from ...) and date_part
    "current_timestamp", # now() and current_timestamp
    "current_date",
    "age",
    "time_to_str",       # to_char(date, 'YYYY-MM')
    "str_to_date",       # to_date(text, 'YYYY-MM-DD')
    "str_to_time",       # to_timestamp(text, format)
    # logic and types
    "coalesce", "nullif", "case", "if", "cast", "try_cast", "exists",
})

# Node types that change data or do something other than read. If any of
# these appears ANYWHERE in the tree, the query is refused. Looking at the
# whole tree is what catches a DELETE hidden inside WITH (...).
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge,      # change rows
    exp.Create, exp.Drop, exp.Alter, exp.TruncateTable, # change the schema
    exp.Command,   # anything sqlglot does not understand: EXPLAIN, SHOW, SET, DO ...
    exp.Copy,      # COPY reads and writes files on the server
    exp.Into,      # SELECT ... INTO new_table creates a table
    exp.Lock,      # SELECT ... FOR UPDATE locks rows
)


class UnsafeSql(ValueError):
    """Raised when the SQL breaks a rule. The message says which one."""

def validate(sql: str) -> str:
    """Returns safe SQL, or raises UnsafeSql."""
    # --- Rule 1: it parses, and it is exactly one statement -----------------
    try:
        # parse() returns a list with one tree per statement. "SELECT 1; DROP ..."
        # gives two trees. Empty statements come back as None, so drop those.
        trees = [t for t in sqlglot.parse(sql, read="postgres") if t is not None]
    except SqlglotError as error:   # ParseError and TokenError both inherit from this
        raise UnsafeSql(f"not valid SQL: {error}") from error
    if len(trees) != 1:
        raise UnsafeSql(f"expected exactly one statement, got {len(trees)}")
    tree = trees[0]
    
    # --- Rule 2: the statement is a SELECT ------------------------------------
    # exp.Select covers SELECT and WITH ... SELECT. exp.SetOperation covers
    # UNION, INTERSECT and EXCEPT, which join two SELECTs.
    if not isinstance(tree, (exp.Select, exp.SetOperation)):
        raise UnsafeSql(f"only SELECT is allowed, got {type(tree).__name__}")
    
    # --- Rule 3: nothing in the tree writes ------------------------------------
    # find() walks every node in the tree and returns the first match, or None.
    bad = tree.find(*FORBIDDEN_NODES)
    if bad is not None:
        raise UnsafeSql(f"{type(bad).__name__} is not allowed")
    
    # --- Rule 4: every table is one of our views -------------------------------
    # Names made inside the query by WITH name AS (...) are not real tables,
    # so they are allowed too.
    with_names = {cte.alias for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        # A function used as a table, such as FROM generate_series(1, 10) or
        # FROM dblink(...), is a Table node whose content is not a plain name.
        if not isinstance(table.this, exp.Identifier):
            raise UnsafeSql("functions cannot be used as tables")
        # table.db is the schema in front of the name (raw.olist_orders -> "raw").
        # The views are reached without a schema, so any schema prefix means
        # the query is aiming at something else: raw, pg_catalog, information_schema.
        if table.db or table.catalog:
            raise UnsafeSql(f"schema-qualified table '{table.db}.{table.name}' is not allowed")
        if table.name not in VIEW_NAMES and table.name not in with_names:
            raise UnsafeSql(f"'{table.name}' is not one of the available views")
        
    # --- Rule 5: every function is on the allow-list ---------------------------
    for func in tree.find_all(exp.Func):
        # sqlglot has a class for each function it knows (exp.Count, exp.Sum).
        # A function it does not know is an exp.Anonymous whose .name is the
        # name as written. Most dangerous Postgres functions (set_config, current_setting, query_to_xml, pg_get_viewdef, etc.) arrive that way.
        if isinstance(func, exp.Anonymous):
            name = func.name.lower()
        else:
            name = func.sql_name().lower()
        if name not in ALLOWED_FUNCTIONS:
            raise UnsafeSql(f"function '{name}' is not allowed")
    
    # --- Rule 6: a row limit, always -------------------------------------------
    # Accept the model's own LIMIT only when it is a plain number no bigger
    # than MAX_ROWS. LIMIT ALL, LIMIT 5000 and LIMIT (SELECT ...) are replaced.
    limit = tree.args.get("limit")
    amount = limit.expression if limit is not None else None
    small_enough = (
        isinstance(amount, exp.Literal)
        and not amount.is_string
        and int(amount.this) <= MAX_ROWS
    )
    if not small_enough:
        tree = tree.limit(MAX_ROWS)   # adds LIMIT, or replaces the one that is there
    
    # Write the tree back out as Postgres SQL. What runs is this text, built
    # from the checked tree, never the original string.
    return tree.sql(dialect="postgres")