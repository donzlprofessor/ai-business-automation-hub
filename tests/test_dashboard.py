from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import CorsSettings
from app.db import get_db
from app.main import app, create_app
from app.models import Inquiry


@pytest.fixture
def populated(client):
    records = [
        ("Ada", "sales", "high", "new", "Pricing request", "Interested in a quote"),
        ("Ben", "support", "medium", "in_progress", "Please help", "Password reset"),
        ("Cia", "support", "high", "resolved", "100%_done", None),
        ("Dev", "other", "low", "new", "Hello", None),
        ("Eve", None, "medium", "new", "Unclassified message", None),
    ]
    dependency = app.dependency_overrides[get_db]()
    db = next(dependency)
    for index, (name, category, priority, status, message, summary) in enumerate(records, 1):
        db.add(Inquiry(
            id=UUID(int=index), customer_name=name, email=f"{name.lower()}@example.com",
            category=category, priority=priority, status=status, message=message,
            ai_summary=summary, created_at=datetime(2026, 1, index, tzinfo=UTC),
        ))
    db.commit()
    dependency.close()
    return client


def test_empty_stats_and_page(client):
    stats = client.get("/api/v1/inquiries/stats")
    assert stats.status_code == 200
    assert stats.json() == dict.fromkeys([
        "total", "high_priority", "sales", "support", "other", "unclassified",
        "new", "in_progress", "resolved",
    ], 0)
    assert client.get("/api/v1/inquiries/page").json() == {
        "items": [], "total": 0, "offset": 0, "limit": 20,
    }


def test_stats_aggregate_entire_database(populated):
    assert populated.get("/api/v1/inquiries/stats").json() == {
        "total": 5, "high_priority": 2, "sales": 1, "support": 2, "other": 1,
        "unclassified": 1, "new": 3, "in_progress": 1, "resolved": 1,
    }


def test_page_and_legacy_contract(populated):
    page = populated.get("/api/v1/inquiries/page?limit=2&offset=2").json()
    assert page["total"] == 5
    assert page["limit"] == 2 and page["offset"] == 2
    assert [row["customer_name"] for row in page["items"]] == ["Cia", "Ben"]
    assert populated.get("/api/v1/inquiries?limit=2&offset=2").json() == page["items"]
    beyond = populated.get("/api/v1/inquiries/page?offset=100").json()
    assert beyond["items"] == [] and beyond["total"] == 5


@pytest.mark.parametrize(("query", "names"), [
    ("category=support", ["Cia", "Ben"]),
    ("category=unclassified", ["Eve"]),
    ("priority=high", ["Cia", "Ada"]),
    ("status=in_progress", ["Ben"]),
    ("category=support&priority=high&status=resolved", ["Cia"]),
    ("category=sales&priority=low", []),
    ("search=ADA", ["Ada"]),
    ("search=ben%40example.com", ["Ben"]),
    ("search=reset", ["Ben"]),
    ("search=pricing", ["Ada"]),
    ("search=%25", ["Cia"]),
    ("search=_", ["Cia"]),
    ("search=%27%20OR%201%3D1--", []),
    ("sort_by=customer_name&sort_dir=asc", ["Ada", "Ben", "Cia", "Dev", "Eve"]),
    ("sort_by=priority&sort_dir=desc", ["Cia", "Ada", "Eve", "Ben", "Dev"]),
    ("sort_by=priority&sort_dir=asc", ["Dev", "Eve", "Ben", "Cia", "Ada"]),
    ("sort_by=created_at&sort_dir=asc", ["Ada", "Ben", "Cia", "Dev", "Eve"]),
])
def test_filters_search_and_sort(populated, query, names):
    response = populated.get(f"/api/v1/inquiries/page?{query}")
    assert response.status_code == 200
    assert [row["customer_name"] for row in response.json()["items"]] == names
    assert response.json()["total"] == len(names)


@pytest.mark.parametrize("query", [
    "limit=101", "limit=0", "offset=-1", "category=invalid", "priority=urgent",
    "status=unknown", "sort_by=email", "sort_dir=sideways", "search=" + "a" * 201,
])
def test_read_validation(client, query):
    assert client.get(f"/api/v1/inquiries/page?{query}").status_code == 422
    assert client.get(f"/api/v1/inquiries?{query}").status_code == 422


def test_cors_explicit_origins(client):
    allowed = client.get("/api/v1/inquiries/stats", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    disallowed = client.get("/api/v1/inquiries/stats", headers={"Origin": "https://unknown.test"})
    assert "access-control-allow-origin" not in disallowed.headers


def test_cors_custom_and_empty_origins():
    with TestClient(create_app(CorsSettings(_env_file=None, cors_origins=["https://dashboard.test"]))) as browser:
        response = browser.options("/api/v1/inquiries/page", headers={
            "Origin": "https://dashboard.test", "Access-Control-Request-Method": "GET",
        })
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://dashboard.test"
    with TestClient(create_app(CorsSettings(_env_file=None, cors_origins=[]))) as browser:
        response = browser.options("/api/v1/inquiries/page", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET",
        })
        assert response.status_code == 400


@pytest.mark.parametrize("origin", ["*", "https://*.test", "https://site.test/path", "file:///tmp"])
def test_cors_rejects_wildcard_and_non_origins(origin):
    with pytest.raises(ValidationError):
        CorsSettings(_env_file=None, cors_origins=[origin])
