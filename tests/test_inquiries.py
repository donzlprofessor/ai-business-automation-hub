from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import app

PAYLOAD = {
    "customer_name": "  Ada Lovelace  ",
    "email": "ada@example.com",
    "message": "  Please tell me about your services.  ",
}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_unavailable_database(client):
    class BrokenSession:
        def execute(self, statement):
            raise OperationalError("SELECT 1", {}, Exception("private connection details"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy"}


def test_create_list_and_retrieve(client):
    assert client.get("/api/v1/inquiries").json() == []
    response = client.post("/api/v1/inquiries", json=PAYLOAD)
    assert response.status_code == 201
    inquiry = response.json()
    assert inquiry["customer_name"] == "Ada Lovelace"
    assert inquiry["message"] == PAYLOAD["message"].strip()
    assert inquiry["email"] == "ada@example.com"
    assert inquiry["status"] == "new"
    assert inquiry["priority"] == "medium"
    assert inquiry["category"] is None
    assert inquiry["ai_summary"] is None
    assert inquiry["created_at"]
    assert client.get(f"/api/v1/inquiries/{inquiry['id']}").json() == inquiry
    assert client.get("/api/v1/inquiries").json() == [inquiry]
    assert client.get("/api/v1/inquiries?offset=1").json() == []


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"customer_name": " "}, {"message": "\n"},
    {"message": "a" * 10001}, {"customer_name": "a" * 201},
    {"status": "resolved"}, {"ai_summary": 123}, {"ai_summary": " "},
    {"ai_summary": "a" * 10001}, {"category": "billing"}, {"category": 1},
    {"priority": "normal"}, {"priority": "urgent"}, {"priority": None},
    {"priority": "MEDIUM"}, {"priority": 1}, {"unknown": "field"},
])
def test_reject_invalid_input(client, changes):
    assert client.post("/api/v1/inquiries", json=PAYLOAD | changes).status_code == 422
    assert client.get("/api/v1/inquiries").json() == []


def test_not_found_and_invalid_id(client):
    assert client.get(f"/api/v1/inquiries/{uuid4()}").status_code == 404
    assert client.get("/api/v1/inquiries/not-a-uuid").status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_pagination_bounds(client, query):
    assert client.get(f"/api/v1/inquiries?{query}").status_code == 422


@pytest.mark.parametrize("category", ["sales", "support", "other"])
@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_classified_inquiry(client, category, priority):
    payload = PAYLOAD | {
        "category": category, "priority": priority, "ai_summary": "Customer requests help.",
    }
    response = client.post("/api/v1/inquiries", json=payload)
    assert response.status_code == 201
    inquiry = response.json()
    for field in ("category", "priority", "ai_summary"):
        assert inquiry[field] == payload[field]
    assert inquiry["status"] == "new"
    assert client.get(f"/api/v1/inquiries/{inquiry['id']}").json() == inquiry
    assert client.get("/api/v1/inquiries").json() == [inquiry]


@pytest.mark.parametrize("classification", [
    {"category": "support"}, {"priority": "high"}, {"ai_summary": "  Help requested.  "},
    {"category": None, "ai_summary": None},
])
def test_partial_classification(client, classification):
    response = client.post("/api/v1/inquiries", json=PAYLOAD | classification)
    assert response.status_code == 201
    inquiry = response.json()
    assert inquiry["category"] == classification.get("category")
    assert inquiry["priority"] == classification.get("priority", "medium")
    summary = classification.get("ai_summary")
    assert inquiry["ai_summary"] == (summary.strip() if summary else None)
