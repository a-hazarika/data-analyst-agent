"""
The first group needs no database. The last group connects as the read-only
login. Those tests take the two_sellers fixture from conftest.py, which skips
them when the database or the login is not there.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from validator import MAX_ROWS, UnsafeSql, validate

# ---------------------------------------------------------------- no database

# Each of these must be refused. parametrize runs the same test once per item
# and reports each one separately.
UNSAFE = [
    "DELETE FROM orders",                                             # 1 not a SELECT
    "SELECT 1; DROP TABLE orders",                                    # 2 two statements
    "SELECT * FROM raw.olist_orders",                                 # 3 a real table
    "SELECT * FROM pg_catalog.pg_tables",                             # 4 system catalog
    "SELECT * FROM pg_tables",                                        # 5 system view, no schema
    "SELECT set_config('app.seller_id', 'someone-else', false)",      # 6 change the seller
    "SELECT pg_sleep(60)",                                            # 7 tie up a connection
    "WITH gone AS (DELETE FROM orders RETURNING *) SELECT * FROM gone",  # 8 a write hidden in WITH
    # more of the same idea
    "SELECT current_setting('app.seller_id')",
    "SELECT * INTO copy_of_orders FROM orders",
    "SELECT * FROM orders FOR UPDATE",
    "SELECT * FROM generate_series(1, 1000000)",
    "SELECT * FROM information_schema.columns",
    "EXPLAIN SELECT * FROM orders",
    "UPDATE orders SET status = 'x'",
    "this is not sql",
    "SELECT query_to_xml('SELECT * FROM raw.olist_orders', true, true, '')",
    "SELECT pg_get_viewdef('api.orders')",
    "",
]


@pytest.mark.parametrize("sql", UNSAFE)
def test_unsafe_sql_is_refused(sql):
    with pytest.raises(UnsafeSql):
        validate(sql)


def test_missing_limit_is_added():                                    # 9
    assert validate("SELECT * FROM orders").endswith(f"LIMIT {MAX_ROWS}")


def test_large_limit_is_replaced():
    assert validate("SELECT * FROM orders LIMIT 100000").endswith(f"LIMIT {MAX_ROWS}")
    assert validate("SELECT * FROM orders LIMIT ALL").endswith(f"LIMIT {MAX_ROWS}")


def test_small_limit_is_kept():
    assert validate("SELECT * FROM orders LIMIT 5").endswith("LIMIT 5")


def test_ordinary_questions_pass():
    # A guardrail that refuses good queries is also broken. These are the
    # shapes the model writes most often.
    validate("SELECT count(*) FROM orders WHERE status = 'delivered'")
    validate(
        "SELECT date_trunc('month', o.ordered_at) AS month, sum(i.price) AS revenue "
        "FROM orders o JOIN order_items i ON i.order_id = o.order_id GROUP BY 1 ORDER BY 1"
    )
    validate(
        "WITH per_order AS (SELECT order_id, sum(price) AS total FROM order_items GROUP BY order_id) "
        "SELECT round(avg(total), 2) FROM per_order"
    )
    validate("SELECT status FROM orders UNION SELECT 'none'")


# ------------------------------------------------------------- with a database

def count_as(seller_id):
    """How many order_items rows the read-only login sees for this seller."""
    from db import ro_engine
    with ro_engine.begin() as conn:
        if seller_id is not None:
            conn.execute(text("SELECT set_config('app.seller_id', :s, true)"), {"s": seller_id})
        return conn.execute(text("SELECT count(*) FROM order_items")).scalar_one()


def test_seller_sees_only_own_rows(two_sellers):                      # 10
    from db import engine
    seller_a, seller_b = two_sellers
    with engine.connect() as conn:   # the owner login can read the real table to get the truth
        real_a = conn.execute(text(
            "SELECT count(*) FROM raw.olist_order_items WHERE seller_id = :s"), {"s": seller_a}).scalar_one()
        real_b = conn.execute(text(
            "SELECT count(*) FROM raw.olist_order_items WHERE seller_id = :s"), {"s": seller_b}).scalar_one()
    assert count_as(seller_a) == real_a      # all of A's rows and nothing else
    assert count_as(seller_b) == real_b
    assert count_as(None) == 0               # no seller set: no rows, not an error


def test_database_refuses_what_the_validator_would_miss(two_sellers):
    """The second lock: even with no validator, the read-only login cannot do harm."""
    from db import ro_engine
    attempts = [
        "SELECT * FROM raw.olist_orders",          # no permission on the raw schema
        "DELETE FROM order_items",                 # read-only transactions
        "CREATE TABLE api.x (a int)",              # cannot create anything
        "SELECT pg_sleep(10)",                     # stopped by the 5 second timeout
    ]
    for sql in attempts:
        with pytest.raises(SQLAlchemyError):
            with ro_engine.begin() as conn:
                conn.execute(text(sql))
