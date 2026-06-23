from api.schemas import TaskResponse


class InMemoryStorage:
    def __init__(self) -> None:
        self._tasks: dict[int, TaskResponse] = {}
        self._next_id: int = 1

    def save(self, task: TaskResponse) -> TaskResponse:
        self._tasks[task.id] = task
        return task

    def get(self, task_id: int) -> TaskResponse | None:
        return self._tasks.get(task_id)

    def list_all(self) -> list[TaskResponse]:
        return list(self._tasks.values())

    def next_id(self) -> int:
        current = self._next_id
        self._next_id += 1
        return current
