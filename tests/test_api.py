import os

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test_tickets.db"
    os.environ["DATABASE_PATH"] = str(database_path)
    config.get_settings.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    os.environ.pop("DATABASE_PATH", None)
    config.get_settings.cache_clear()


def test_create_and_get_ticket(client: TestClient):
    create_response = client.post(
        "/tickets",
        json={
            "title": "Login issue",
            "description": "A customer cannot access the dashboard.",
            "priority": "high",
        },
    )
    assert create_response.status_code == 201
    created_ticket = create_response.json()

    get_response = client.get(f"/tickets/{created_ticket['id']}")
    assert get_response.status_code == 200
    fetched_ticket = get_response.json()

    assert fetched_ticket["title"] == "Login issue"
    assert fetched_ticket["priority"] == "high"
    assert fetched_ticket["status"] == "open"


def test_filter_and_search_tickets(client: TestClient):
    client.post(
        "/tickets",
        json={
            "title": "Password reset",
            "description": "Reset link fails for one user.",
            "priority": "medium",
        },
    )
    client.post(
        "/tickets",
        json={
            "title": "Checkout failure",
            "description": "Payment flow is failing for multiple customers.",
            "priority": "urgent",
        },
    )

    search_response = client.get("/tickets", params={"search": "payment"})
    assert search_response.status_code == 200
    items = search_response.json()

    assert len(items) == 1
    assert items[0]["title"] == "Checkout failure"

    priority_response = client.get("/tickets", params={"priority": "urgent"})
    assert priority_response.status_code == 200
    assert len(priority_response.json()) == 1


def test_patch_status_and_metrics(client: TestClient):
    create_response = client.post(
        "/tickets",
        json={
            "title": "Deployment warning",
            "description": "Logs show repeated deployment warnings.",
            "priority": "low",
        },
    )
    ticket_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "in_progress", "priority": "high"},
    )
    assert patch_response.status_code == 200
    updated_ticket = patch_response.json()
    assert updated_ticket["status"] == "in_progress"
    assert updated_ticket["priority"] == "high"

    status_response = client.put(
        f"/tickets/{ticket_id}/status",
        json={"status": "resolved"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "resolved"

    metrics_response = client.get("/tickets/metrics/summary")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["total"] == 1
    assert metrics["resolved"] == 1


def test_delete_missing_ticket_returns_404(client: TestClient):
    response = client.delete("/tickets/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"

