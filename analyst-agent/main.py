from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import Document, get_session
from sql_agent import ask_sql, uses_only_views

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
    if not uses_only_views(result.sql):
        raise HTTPException(status_code=400, detail="The generated SQL used a table that is not allowed.")
    # result is a SqlResult; model_dump() turns it into a dict whose keys
    # match AskResponse's fields.
    return AskResponse(**result.model_dump())

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
