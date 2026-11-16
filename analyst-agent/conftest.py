"""Shared test helpers. pytest loads this file by itself; anything marked
@pytest.fixture here can be used by any test by naming it as an argument."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture
def two_sellers():
    """Two real seller ids from the data.

    Tests that use this need the database, the views and the analyst_ro
    login. When any of those is missing the test is skipped, not failed, so
    `uv run pytest` still works on a machine without Postgres.
    """
    try:
        from db import engine, ro_engine
        with engine.connect() as conn:
            # The two sellers with the most items, so both have rows to see.
            ids = conn.execute(text(
                "SELECT seller_id FROM raw.olist_order_items "
                "GROUP BY seller_id ORDER BY count(*) DESC, seller_id LIMIT 2"
            )).scalars().all()
        with ro_engine.begin() as conn:    # proves the login works and the views exist
            conn.execute(text("SELECT 1 FROM order_items LIMIT 1"))
    except SQLAlchemyError as error:
        pytest.skip(f"database, views or analyst_ro login not available: {error}")
    if len(ids) < 2:
        pytest.skip("need at least two sellers in raw.olist_order_items")
    return ids
