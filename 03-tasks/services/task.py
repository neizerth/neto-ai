from datetime import datetime, timezone

from api.schemas import TaskCreate, TaskResponse
from services.storage import InMemoryStorage

_storage = InMemoryStorage()


class TaskService:
    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    def create_task(self, payload: TaskCreate) -> TaskResponse:
        task = TaskResponse(
            id=self._storage.next_id(),
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            created_at=datetime.now(timezone.utc),
        )
        return self._storage.save(task)

    def get_task(self, task_id: int) -> TaskResponse | None:
        return self._storage.get(task_id)

    def list_tasks(self) -> list[TaskResponse]:
        return self._storage.list_all()


def get_task_service() -> TaskService:
    return TaskService(storage=_storage)
