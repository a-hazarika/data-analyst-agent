from pathlib import Path

import anthropic                      # the official Claude SDK
import sqlglot                        # SQL parser, used to inspect what the model wrote
import yaml
from pydantic import BaseModel
from sqlglot import exp               # exp holds the node types of a parsed query (Table, CTE, ...)

from schema_text import schema_text   # step 5: the catalog as plain text
from settings import settings

# The set of view names the model is allowed to use, read once from the catalog.
# Example: {"orders", "order_items", "customers"}
VIEW_NAMES = set(yaml.safe_load(Path("catalog.yaml").read_text(encoding="utf-8"))["views"])

# The instructions that go in front of the schema. This is the part to keep
# improving: when a question fails, the fix is usually a clearer rule here
# or a clearer column description in catalog.yaml.
RULES = """You write PostgreSQL queries for a marketplace seller's data.

Rules:
- Write exactly one SELECT statement. Never write INSERT, UPDATE, DELETE or DDL.
- Use only the views and columns listed below. They are the whole database.
- Join views only on the links listed under "How the views join".
- The data is already limited to the current seller. Do not filter by seller.
- Money is in BRL. Dates are timestamps; use date_trunc for months and days.
- If the question cannot be answered from these views, return the SQL
  SELECT 'cannot answer' AS reason and explain why in the explanation.
"""

class SqlAnswer(BaseModel):
    sql: str
    explanation: str
    
class SqlResult(BaseModel):
    """What ask_sql returns to the rest of the app."""
    sql: str
    explanation: str
    input_tokens: int   # tokens we sent (rules + schema + question)
    output_tokens: int  # tokens the model wrote    

def call_model(question: str):
    """Sends the question to Claude and returns the raw response.

    Kept as its own small function so tests can replace it with a fake.
    """
    # Create the client here, not at import time, so importing this file
    # never needs an API key (tests and CI rely on that).
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return client.messages.parse(
        model=settings.model_name,          # which Claude model
        max_tokens=1000,                    # upper limit on the reply's length
        system=RULES + "\n" + schema_text(),  # standing instructions + the views       
        messages=[{"role": "user", "content": question}],  # the user's question
        output_format=SqlAnswer
    )



def ask_sql(question: str) -> SqlResult:
    """Question in, SQL and explanation out."""
    response = call_model(question)
    # stop_reason says why the model stopped. "end_turn" is the normal case.
    # "max_tokens" means the reply was cut off, and "refusal" means the model
    # declined; in both cases the JSON may be missing or incomplete.
    if response.stop_reason in ("max_tokens", "refusal") or response.parsed_output is None:
        raise ValueError(f"No usable answer from the model (stop_reason: {response.stop_reason})")
    answer = response.parsed_output           # already a validated SqlAnswer
    return SqlResult(
        sql=answer.sql.strip().rstrip(";"),   # tidy: no surrounding spaces, no trailing semicolon
        explanation=answer.explanation,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

def tables_used(sql: str) -> set[str]:
    """Parses the SQL and returns the names of the tables or views it reads.

    Raises sqlglot.errors.ParseError if the SQL is not valid PostgreSQL.
    A name with a schema in front (raw.olist_orders) is returned with the
    schema, so it can never match a view name by accident.
    """
    tree = sqlglot.parse_one(sql, read="postgres")       # text -> tree of nodes
    # Names defined inside the query itself by WITH name AS (...). These are
    # not real tables, so leave them out.
    with_names = {cte.alias for cte in tree.find_all(exp.CTE)}
    names = set()
    for table in tree.find_all(exp.Table):               # every table reference in the tree
        full = f"{table.db}.{table.name}" if table.db else table.name
        if full not in with_names:
            names.add(full)
    return names


def uses_only_views(sql: str) -> bool:
    """True when every table in the SQL is a view from the catalog."""
    return tables_used(sql) <= VIEW_NAMES                # "<=" on sets means "is a subset of"