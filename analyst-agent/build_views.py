"""Generates the api.* views from catalog.yaml. Safe to run again after editing the catalog.

Run from the analyst-agent folder:  uv run python build_views.py
"""
import re
from pathlib import Path

import yaml
from sqlalchemy import text

from db import engine  # the owner connection, never the read-only one

SELLER = "current_setting('app.seller_id', true)"
NAME = re.compile(r"^[a-z_][a-z0-9_]*$")          # view and column names
SOURCE = re.compile(r"^[a-z_]+\.[a-z_][a-z0-9_]*$")  # schema.table

# How each scope limits a view to the signed-in seller. {t} is the source table's alias.
SCOPES = {
    "none": "",
    "direct": f"WHERE t.seller_id = {SELLER}",
    "via_order": (
        "WHERE EXISTS (SELECT 1 FROM raw.olist_order_items i "
        f"WHERE i.order_id = t.order_id AND i.seller_id = {SELLER})"
    ),
    "via_customer": (
        "WHERE EXISTS (SELECT 1 FROM raw.olist_orders o "
        "JOIN raw.olist_order_items i ON i.order_id = o.order_id "
        f"WHERE o.customer_id = t.customer_id AND i.seller_id = {SELLER})"
    ),
}

def view_sql(name: str, view: dict) -> list[str]:
    """Returns the statements that (re)create one view."""
    if not NAME.match(name) or not SOURCE.match(view["source"]):
        raise ValueError(f"bad view name or source: {name} / {view['source']}")
    scope = view.get("scope", "none")
    if scope not in SCOPES:
        raise ValueError(f"{name}: unknown scope '{scope}', use one of {list(SCOPES)}")

    select_list = []
    for column, spec in view["columns"].items():
        if not NAME.match(column) or not NAME.match(spec["source"]):
            raise ValueError(f"{name}: bad column name {column} / {spec['source']}")
        select_list.append(f"t.{spec['source']} AS {column}")

    statements = [
        f"DROP VIEW IF EXISTS api.{name} CASCADE",
        f"CREATE VIEW api.{name} WITH (security_barrier) AS "
        f"SELECT {', '.join(select_list)} FROM {view['source']} t {SCOPES[scope]}",
    ]
    return statements

def build(catalog_path: str = "catalog.yaml") -> list[str]:
    catalog = yaml.safe_load(Path(catalog_path).read_text(encoding="utf-8"))
    built = []
    with engine.begin() as conn:  # one transaction: all views or none
        for name, view in catalog["views"].items():
            for statement in view_sql(name, view):
                conn.execute(text(statement))
            built.append(name)
        # Dropping a view drops its grants, so give them back if the read-only login exists (day 4).
        if conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'analyst_ro'")).first():
            conn.execute(text("GRANT USAGE ON SCHEMA api TO analyst_ro"))
            conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA api TO analyst_ro"))
    return built


if __name__ == "__main__":
    print("built views:", ", ".join(build()))
