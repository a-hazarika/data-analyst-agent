"""read-only role

Revision ID: 73c12bfc5fa0
Revises: a753063ac436
Create Date: 2026-11-16 14:07:46.208009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy import text
from sqlalchemy.engine import make_url
from settings import settings

# revision identifiers, used by Alembic.
revision: str = '73c12bfc5fa0'
down_revision: Union[str, Sequence[str], None] = 'a753063ac436'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The password comes from READONLY_DATABASE_URL (in .env, never in Git)
    password = make_url(settings.readonly_database_url).password
    if not password:
        raise RuntimeError("READONLY_DATABASE_URL has no password")
    
    # CREATE ROLE AND ALTER ROLE cannot take bound parameters. So pass the 
    # password as a parameter into a setting that lasts for this transaction,
    # and let Postgres quote it safely with format('%L')
    bind = op.get_bind()
    bind.execute(text("SELECT set_config('app.ro_password', :p, true)"), {"p": password})
    # A role belongs to the whole Postgres server, not to one database, so it
    # may already exist (for example if you created it by hand). The DO block
    # creates it only when it is missing, which makes the migration safe to run
    # on any machine.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analyst_ro') THEN
                CREATE ROLE analyst_ro LOGIN;
            END IF;
            EXECUTE format('ALTER ROLE analyst_ro PASSWORD %L', current_setting('app.ro_password'));
        END
        $$;
    """)
    # By default every login may create tables in the public schema. Remove that.
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    # The api schema holds the views. It is created by db/01_schema.sql; this
    # line only matters on a database where that script has not run yet.
    op.execute("CREATE SCHEMA IF NOT EXISTS api")
    # USAGE lets the role look inside the schema; SELECT lets it read the views.
    op.execute("GRANT USAGE ON SCHEMA api TO analyst_ro")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA api TO analyst_ro")
    # Views created later in api get SELECT for analyst_ro automatically.
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA api GRANT SELECT ON TABLES TO analyst_ro")
    # An unqualified name such as "orders" resolves to api.orders and nothing else.
    op.execute("ALTER ROLE analyst_ro SET search_path = api")
    # Any query is cancelled after 5 seconds.
    op.execute("ALTER ROLE analyst_ro SET statement_timeout = '5s'")
    # Every transaction is read-only, so INSERT, UPDATE, DELETE and CREATE all fail.
    op.execute("ALTER ROLE analyst_ro SET default_transaction_read_only = on")


def downgrade() -> None:
    # Give back what upgrade() took, then remove the role and everything granted to it.
    op.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA api REVOKE SELECT ON TABLES FROM analyst_ro")
    op.execute("DROP OWNED BY analyst_ro")
    op.execute("DROP ROLE IF EXISTS analyst_ro")
