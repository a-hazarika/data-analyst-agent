from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status":"ok"}
    
def test_short_question_is_rejected():
    assert client.post("/ask", json={"question":"hi"}).status_code == 422
    