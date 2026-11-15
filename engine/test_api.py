from fastapi.testclient import TestClient
from app import app
c = TestClient(app)
print(c.get("/health").json())
for t in ["bomba la jikoni linavuja", "my AC is not cooling", "stima imekatika sebuleni", "I need a painter", "hello"]:
    print(t, "->", c.post("/diagnose", json={"text": t}).json())
print("empty text ->", c.post("/diagnose", json={"text": ""}).status_code)
print("missing field ->", c.post("/diagnose", json={}).status_code)
