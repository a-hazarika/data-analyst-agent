from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from settings import settings

# The owner connection: migrations, build_views.py, documents, and tests that
# need to see the real tables. It can do anything, so it never runs SQL the
# model wrote.
engine = create_engine(settings.database_url)

# Day 4: the read-only connection. It logs in as analyst_ro, which can only
# SELECT from the api views. This is the ONLY engine that runs model-written SQL.
# Creating an engine does not connect; the first query does. So importing
# this file works even before the analyst_ro login exists.
ro_engine = create_engine(settings.readonly_database_url)

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str]

def get_session():
    with Session(engine) as session:
        yield session