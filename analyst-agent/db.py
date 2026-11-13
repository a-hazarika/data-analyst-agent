from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from settings import settings

engine = create_engine(settings.database_url)
# engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5436/analyst")

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