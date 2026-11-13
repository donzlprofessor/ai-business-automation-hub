from itertools import product
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import Update, select

from app.db import get_db
from app.main import app
from app.models import Inquiry

PAYLOAD = {
    "customer_name": "Status Test", "email": "status@example.com", "message": "Help requested.",
    "category": "support", "priority": "high", "ai_summary": "Customer needs help.",
}
STATES = ["new", "in_progress", "resolved"]


@pytest.mark.parametrize(("initial", "target"), list(product(STATES, repeat=2)))
def test_transition_matrix(client, initial, target):
    inquiry = client.post("/api/v1/inquiries", json=PAYLOAD).json()
    dependency = app.dependency_overrides[get_db]()
    db = next(dependency)
    db.scalar(select(Inquiry)).status = initial
    db.commit()
    dependency.close()

    response = client.patch(f"/api/v1/inquiries/{inquiry['id']}/status", json={
        "status": target, "expected_status": initial,
    })
    allowed = initial == target or (initial, target) in {
        ("new", "in_progress"), ("in_progress", "resolved"), ("resolved", "in_progress"),
    }
    assert response.status_code == (200 if allowed else 409)
    stored = client.get(f"/api/v1/inquiries/{inquiry['id']}").json()
    assert stored == inquiry | {"status": target if allowed else initial}


def test_status_only_payload_and_reopen_refresh_stats_and_filters(client):
    inquiry = client.post("/api/v1/inquiries", json=PAYLOAD).json()
    url = f"/api/v1/inquiries/{inquiry['id']}/status"
    for target in ["in_progress", "resolved", "in_progress"]:
        assert client.patch(url, json={"status": target}).status_code == 200
        stats = client.get("/api/v1/inquiries/stats").json()
        assert stats[target] == 1
        assert sum(stats[state] for state in STATES) == 1
        page = client.get(f"/api/v1/inquiries/page?status={target}").json()
        assert page["total"] == 1 and page["items"][0]["status"] == target


def test_stale_update_is_rejected_even_if_target_would_be_valid(client):
    inquiry = client.post("/api/v1/inquiries", json=PAYLOAD).json()
    url = f"/api/v1/inquiries/{inquiry['id']}/status"
    assert client.patch(url, json={"status": "in_progress"}).status_code == 200
    assert client.patch(url, json={"status": "resolved"}).status_code == 200
    response = client.patch(url, json={"status": "in_progress", "expected_status": "new"})
    assert response.status_code == 409
    assert client.get(f"/api/v1/inquiries/{inquiry['id']}").json()["status"] == "resolved"


def test_concurrent_write_after_read_is_not_overwritten(client, monkeypatch):
    inquiry = client.post("/api/v1/inquiries", json=PAYLOAD).json()
    dependency = app.dependency_overrides[get_db]()
    db = next(dependency)
    execute = db.execute

    def concurrent_write(statement, *args, **kwargs):
        if isinstance(statement, Update):
            # Simulate another writer winning the compare-and-set after our read.
            return SimpleNamespace(rowcount=0)
        return execute(statement, *args, **kwargs)

    monkeypatch.setattr(db, "execute", concurrent_write)
    app.dependency_overrides[get_db] = lambda: db
    response = client.patch(f"/api/v1/inquiries/{inquiry['id']}/status", json={
        "status": "in_progress", "expected_status": "new",
    })
    assert response.status_code == 409
    assert client.get(f"/api/v1/inquiries/{inquiry['id']}").json() == inquiry
    dependency.close()


@pytest.mark.parametrize("payload", [
    {}, {"status": None}, {"status": "closed"}, {"status": 1},
    {"status": "in_progress", "expected_status": "unknown"},
    {"status": "in_progress", "message": "overwritten"},
])
def test_strict_status_payload(client, payload):
    inquiry = client.post("/api/v1/inquiries", json=PAYLOAD).json()
    assert client.patch(f"/api/v1/inquiries/{inquiry['id']}/status", json=payload).status_code == 422
    assert client.get(f"/api/v1/inquiries/{inquiry['id']}").json() == inquiry


def test_status_missing_and_malformed_ids(client):
    assert client.patch(f"/api/v1/inquiries/{uuid4()}/status", json={"status": "in_progress"}).status_code == 404
    assert client.patch("/api/v1/inquiries/invalid/status", json={"status": "in_progress"}).status_code == 422


def test_cors_allows_status_json_for_local_frontend(client):
    response = client.options("/api/v1/inquiries/any/status", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "PATCH",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = client.options("/api/v1/inquiries/any/status", headers={
        "Origin": "https://unknown.test", "Access-Control-Request-Method": "PATCH",
    })
    assert denied.status_code == 400
