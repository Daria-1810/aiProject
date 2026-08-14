import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

API = "/api/v1/tasks"


def _create(client: TestClient, **overrides) -> dict:
    payload = {"title": "Test task"}
    payload.update(overrides)
    response = client.post(API, json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_task_minimal(client: TestClient) -> None:
    response = client.post(API, json={"title": "Buy milk"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["description"] is None
    assert body["status"] == "todo"
    uuid.UUID(body["id"])
    assert body["created_at"] == body["updated_at"]


def test_create_task_all_fields(client: TestClient) -> None:
    response = client.post(
        API,
        json={"title": "Write report", "description": "Q3 summary", "status": "in_progress"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["description"] == "Q3 summary"
    assert body["status"] == "in_progress"


def test_create_task_missing_title(client: TestClient) -> None:
    response = client.post(API, json={})
    assert response.status_code == 422


def test_create_task_title_too_long(client: TestClient) -> None:
    response = client.post(API, json={"title": "a" * 201})
    assert response.status_code == 422


def test_create_task_empty_title(client: TestClient) -> None:
    response = client.post(API, json={"title": ""})
    assert response.status_code == 422


def test_create_task_blank_title(client: TestClient) -> None:
    response = client.post(API, json={"title": "   "})
    assert response.status_code == 422


def test_create_task_invalid_status(client: TestClient) -> None:
    response = client.post(API, json={"title": "Task", "status": "not_a_status"})
    assert response.status_code == 422


def test_list_tasks_empty(client: TestClient) -> None:
    response = client.get(API)
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_created(client: TestClient) -> None:
    _create(client, title="First")
    _create(client, title="Second")
    response = client.get(API)
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["First", "Second"]


def test_get_task_success(client: TestClient) -> None:
    task = _create(client, title="Read book")
    response = client.get(f"{API}/{task['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == task["id"]


def test_get_task_not_found(client: TestClient) -> None:
    response = client.get(f"{API}/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_task_invalid_uuid(client: TestClient) -> None:
    response = client.get(f"{API}/not-a-uuid")
    assert response.status_code == 422


def test_patch_task_single_field(client: TestClient) -> None:
    task = _create(client, title="Old title")
    response = client.patch(f"{API}/{task['id']}", json={"title": "New title"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["description"] is None
    assert body["status"] == "todo"


def test_patch_task_multiple_fields(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(
        f"{API}/{task['id']}",
        json={"description": "Details", "status": "done"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Details"
    assert body["status"] == "done"
    assert body["title"] == "Task"


def test_patch_task_updates_updated_at(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(f"{API}/{task['id']}", json={"status": "done"})
    assert response.status_code == 200
    body = response.json()
    assert body["created_at"] == task["created_at"]
    assert body["updated_at"] != task["updated_at"]


def test_patch_task_updated_at_is_monotonic_when_clock_does_not_advance(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _create(client, title="Task")
    frozen = datetime.fromisoformat(task["updated_at"])
    monkeypatch.setattr("app.crud.task._utcnow", lambda: frozen)

    response = client.patch(f"{API}/{task['id']}", json={"title": "Changed"})
    assert response.status_code == 200
    body = response.json()
    assert body["updated_at"] != task["updated_at"]
    assert datetime.fromisoformat(body["updated_at"]) > frozen


def test_patch_task_empty_body_is_noop(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(f"{API}/{task['id']}", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == task["title"]
    assert body["description"] == task["description"]
    assert body["status"] == task["status"]


def test_patch_task_not_found(client: TestClient) -> None:
    response = client.patch(f"{API}/{uuid.uuid4()}", json={"title": "X"})
    assert response.status_code == 404


def test_patch_task_invalid_status(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(f"{API}/{task['id']}", json={"status": "bogus"})
    assert response.status_code == 422


def test_patch_task_null_title_rejected(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(f"{API}/{task['id']}", json={"title": None})
    assert response.status_code == 422


def test_delete_task(client: TestClient) -> None:
    task = _create(client, title="To delete")
    response = client.delete(f"{API}/{task['id']}")
    assert response.status_code == 204
    response = client.get(f"{API}/{task['id']}")
    assert response.status_code == 404


def test_delete_task_not_found(client: TestClient) -> None:
    response = client.delete(f"{API}/{uuid.uuid4()}")
    assert response.status_code == 404


def _future(**kwargs) -> str:
    return (datetime.now(timezone.utc) + timedelta(**kwargs)).isoformat()


def _past(**kwargs) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat()


def test_create_task_with_due_at(client: TestClient) -> None:
    response = client.post(API, json={"title": "Task with deadline", "due_at": _future(days=1)})
    assert response.status_code == 201
    assert response.json()["due_at"] is not None


def test_create_task_without_due_at_is_null(client: TestClient) -> None:
    task = _create(client, title="No deadline")
    assert task["due_at"] is None


def test_create_task_due_at_in_past_rejected(client: TestClient) -> None:
    response = client.post(API, json={"title": "Task", "due_at": _past(days=1)})
    assert response.status_code == 422


def test_patch_task_set_due_at(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(f"{API}/{task['id']}", json={"due_at": _future(days=2)})
    assert response.status_code == 200
    assert response.json()["due_at"] is not None


def test_patch_task_clear_due_at_with_null(client: TestClient) -> None:
    task = _create(client, title="Task", due_at=_future(days=1))
    assert task["due_at"] is not None
    response = client.patch(f"{API}/{task['id']}", json={"due_at": None})
    assert response.status_code == 200
    assert response.json()["due_at"] is None


def test_patch_task_due_at_in_past_rejected(client: TestClient) -> None:
    task = _create(client, title="Task")
    response = client.patch(f"{API}/{task['id']}", json={"due_at": _past(days=1)})
    assert response.status_code == 422


def test_list_tasks_filter_due_after(client: TestClient) -> None:
    _create(client, title="Near", due_at=_future(days=1))
    _create(client, title="Far", due_at=_future(days=10))
    _create(client, title="No due")
    response = client.get(API, params={"due_after": _future(days=5)})
    assert response.status_code == 200
    titles = {t["title"] for t in response.json()}
    assert titles == {"Far"}


def test_list_tasks_filter_due_before(client: TestClient) -> None:
    _create(client, title="Near", due_at=_future(days=1))
    _create(client, title="Far", due_at=_future(days=10))
    response = client.get(API, params={"due_before": _future(days=5)})
    assert response.status_code == 200
    titles = {t["title"] for t in response.json()}
    assert titles == {"Near"}


def test_list_tasks_sort_due_at_asc(client: TestClient) -> None:
    _create(client, title="Later", due_at=_future(days=10))
    _create(client, title="Sooner", due_at=_future(days=1))
    response = client.get(API, params={"sort": "due_at", "order": "asc"})
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Sooner", "Later"]


def test_list_tasks_sort_due_at_desc(client: TestClient) -> None:
    _create(client, title="Later", due_at=_future(days=10))
    _create(client, title="Sooner", due_at=_future(days=1))
    response = client.get(API, params={"sort": "due_at", "order": "desc"})
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Later", "Sooner"]


def test_list_tasks_invalid_sort_rejected(client: TestClient) -> None:
    response = client.get(API, params={"sort": "title"})
    assert response.status_code == 422


def test_list_tasks_invalid_order_rejected(client: TestClient) -> None:
    response = client.get(API, params={"sort": "due_at", "order": "sideways"})
    assert response.status_code == 422
