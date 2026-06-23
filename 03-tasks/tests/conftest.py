import pytest
from fastapi.testclient import TestClient

from main import app
from services.storage import InMemoryStorage
from services.task import TaskService, get_task_service


@pytest.fixture
def storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest.fixture
def task_service(storage: InMemoryStorage) -> TaskService:
    return TaskService(storage=storage)


@pytest.fixture
def client(task_service: TaskService):
    app.dependency_overrides[get_task_service] = lambda: task_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
