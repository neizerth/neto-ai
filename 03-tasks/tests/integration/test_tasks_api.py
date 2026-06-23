def test_create_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Test task",
            "description": "Some details",
            "priority": 3,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test task"
    assert data["description"] == "Some details"
    assert data["priority"] == 3
    assert "created_at" in data


def test_create_task_validation_error(client):
    response = client.post(
        "/tasks",
        json={"title": "ab", "priority": 3},
    )

    assert response.status_code == 422


def test_list_tasks_empty(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_after_creation(client):
    client.post("/tasks", json={"title": "Task one", "priority": 1})
    client.post("/tasks", json={"title": "Task two", "priority": 2})

    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_task_found(client):
    created = client.post(
        "/tasks",
        json={"title": "Find me", "priority": 3},
    ).json()

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Find me"


def test_get_task_not_found(client):
    response = client.get("/tasks/999")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["detail"] == "Task not found"
    assert data["detail"]["task_id"] == 999


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
