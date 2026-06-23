import pytest
from pydantic import ValidationError

from api.schemas import TaskCreate, TaskResponse


def test_valid_task_create():
    task = TaskCreate(title="Test task", priority=3)
    assert task.title == "Test task"
    assert task.description is None
    assert task.priority == 3


@pytest.mark.parametrize("title", ["ab", "a", ""])
def test_invalid_title_too_short(title):
    with pytest.raises(ValidationError):
        TaskCreate(title=title, priority=3)


def test_invalid_title_too_long():
    with pytest.raises(ValidationError):
        TaskCreate(title="a" * 101, priority=3)


@pytest.mark.parametrize("priority", [0, 6, -1])
def test_invalid_priority_out_of_range(priority):
    with pytest.raises(ValidationError):
        TaskCreate(title="Valid title", priority=priority)


def test_valid_task_response():
    from datetime import datetime, timezone

    task = TaskResponse(
        id=1,
        title="Test task",
        description=None,
        priority=3,
        created_at=datetime.now(timezone.utc),
    )
    assert task.id == 1
