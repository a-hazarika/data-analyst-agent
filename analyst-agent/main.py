from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import Document, get_session
from sql_agent import ask_sql, uses_only_views
from validator import UnsafeSql, validate

app = FastAPI()

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

class AskResponse(BaseModel):
    sql: str
    explanation: str
    input_tokens: int   
    output_tokens: int 

@app.get("/health")
def health() -> dict[str, str]:
    return { "status": "ok" }

@app.post("/ask")
def ask(body: AskRequest) -> AskResponse:
    result = ask_sql(body.question)
    try:
        # Every query goes through the validator. What comes back is
        # the checked SQL with a row limit; that is what we return (and, from
        # what we run later). The model's original text is never used again.
        safe_sql = validate(result.sql)
    except UnsafeSql as error:
        # 400 = the request could not be served as asked. The message says
        # which rule was broken and contains nothing secret.
        raise HTTPException(status_code=400, detail=f"The generated SQL was refused: {error}")
    return AskResponse(
        sql=safe_sql,
        explanation=result.explanation,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )

@app.get("/documents")
def list_documents(session: Session = Depends(get_session)) -> list[dict]:
    rows  = session.scalars(select(Document).order_by(Document.title)).all()
    return [{ "id": d.id, "title": d.title} for d in rows]

@app.post("/documents")
def add_document(title: str, body: str, session: Session = Depends(get_session)) -> dict:
    doc = Document(title=title, body=body)
    session.add(doc)
    session.commit()
    return {"id": doc.id}
