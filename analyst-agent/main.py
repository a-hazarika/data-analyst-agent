from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import Document, get_session

app = FastAPI()

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

class AskResponse(BaseModel):
    answer: str
    sql: str | None = None

@app.get("/health")
def health() -> dict[str, str]:
    return { "status": "ok" }

@app.post("/ask")
def ask(body: AskRequest) -> AskResponse:
    if "drop" in body.question.lower():
        raise HTTPException(status_code=400, detail="That question is not allowed.")
    return AskResponse(answer=f"You asked: {body.question}")

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
