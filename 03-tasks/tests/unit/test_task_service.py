from api.schemas import TaskCreate
from services.storage import InMemoryStorage
from services.task import TaskService


def test_create_task():
    service = TaskService(storage=InMemoryStorage())
    task = service.create_task(TaskCreate(title="First task", priority=2))

    assert task.id == 1
    assert task.title == "First task"
    assert task.priority == 2
    assert task.created_at is not None


def test_create_multiple_tasks_increment_ids():
    storage = InMemoryStorage()
    service = TaskService(storage=storage)

    first = service.create_task(TaskCreate(title="First task", priority=1))
    second = service.create_task(TaskCreate(title="Second task", priority=2))

    assert first.id == 1
    assert second.id == 2


def test_get_task_found():
    service = TaskService(storage=InMemoryStorage())
    created = service.create_task(TaskCreate(title="Find me", priority=3))

    found = service.get_task(created.id)

    assert found is not None
    assert found.title == "Find me"


def test_get_task_not_found():
    service = TaskService(storage=InMemoryStorage())

    assert service.get_task(999) is None


def test_list_tasks():
    service = TaskService(storage=InMemoryStorage())
    service.create_task(TaskCreate(title="Task one", priority=1))
    service.create_task(TaskCreate(title="Task two", priority=2))

    tasks = service.list_tasks()

    assert len(tasks) == 2
    assert tasks[0].title == "Task one"
    assert tasks[1].title == "Task two"


def test_storage_save_and_get():
    from datetime import datetime, timezone

    from api.schemas import TaskResponse

    storage = InMemoryStorage()
    task = TaskResponse(
        id=storage.next_id(),
        title="Stored task",
        description="Details",
        priority=4,
        created_at=datetime.now(timezone.utc),
    )
    storage.save(task)

    assert storage.get(task.id) == task
    assert storage.list_all() == [task]
