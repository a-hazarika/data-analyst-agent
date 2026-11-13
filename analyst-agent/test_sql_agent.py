"""Step 8: prove the question-to-SQL step works.

Run:               uv run pytest
With the real API:  set RUN_LIVE=1 first (costs a few cents; needs your key in .env)
"""
import os
from types import SimpleNamespace

import pytest
import sqlglot
from fastapi.testclient import TestClient

import sql_agent
from main import app

client = TestClient(app)


def fake_response(sql: str, explanation: str = "test", stop_reason: str = "end_turn"):
    """Builds an object shaped like the SDK's reply, without calling the API."""
    return SimpleNamespace(
        parsed_output=sql_agent.SqlAnswer(sql=sql, explanation=explanation),
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
    )


def test_ask_sql_returns_structured_answer(monkeypatch):
    # monkeypatch swaps call_model for a fake during this one test, so no
    # API key is needed and nothing is spent.
    monkeypatch.setattr(sql_agent, "call_model", lambda q: fake_response("SELECT count(*) FROM orders;"))
    result = sql_agent.ask_sql("How many orders do I have?")
    assert result.sql == "SELECT count(*) FROM orders"   # the trailing semicolon was removed
    assert result.input_tokens == 100


def test_cut_off_reply_is_an_error(monkeypatch):
    # If the model ran out of tokens, ask_sql must fail loudly, not return half an answer.
    monkeypatch.setattr(sql_agent, "call_model", lambda q: fake_response("SELECT 1", stop_reason="max_tokens"))
    with pytest.raises(ValueError):
        sql_agent.ask_sql("anything")


def test_tables_used_finds_views_and_ignores_with_names():
    sql = """
        WITH monthly AS (SELECT date_trunc('month', ordered_at) AS m, order_id FROM orders)
        SELECT m, sum(i.price) FROM monthly JOIN order_items i USING (order_id) GROUP BY m
    """
    assert sql_agent.tables_used(sql) == {"orders", "order_items"}   # "monthly" is not a table


def test_real_table_is_not_allowed():
    assert sql_agent.uses_only_views("SELECT * FROM orders")
    assert not sql_agent.uses_only_views("SELECT * FROM raw.olist_orders")
    assert not sql_agent.uses_only_views("SELECT * FROM pg_tables")


def test_invalid_sql_raises():
    with pytest.raises(sqlglot.errors.ParseError):
        sql_agent.tables_used("SELEC FROM WHERE")


def test_ask_endpoint_returns_sql(monkeypatch):
    monkeypatch.setattr(sql_agent, "call_model", lambda q: fake_response("SELECT count(*) FROM orders"))
    response = client.post("/ask", json={"question": "How many orders do I have?"})
    assert response.status_code == 200
    assert response.json()["sql"] == "SELECT count(*) FROM orders"


def test_ask_endpoint_refuses_real_tables(monkeypatch):
    monkeypatch.setattr(sql_agent, "call_model", lambda q: fake_response("SELECT * FROM raw.olist_orders"))
    assert client.post("/ask", json={"question": "Show me everything"}).status_code == 400


# The three real questions from the roadmap. Skipped unless RUN_LIVE=1.
QUESTIONS = [
    "How many orders were delivered?",
    "What is my total revenue by month?",
    "Which products had the highest shipping cost?",
]


@pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="set RUN_LIVE=1 to call the real model")
@pytest.mark.parametrize("question", QUESTIONS)
def test_live_question_gives_valid_sql(question):
    result = sql_agent.ask_sql(question)
    print(f"\n{question}\n{result.sql}\n{result.explanation}\ninput tokens: {result.input_tokens}")
    assert sql_agent.uses_only_views(result.sql)   # also proves the SQL parses
