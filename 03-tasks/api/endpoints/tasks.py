from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import TaskCreate, TaskResponse, TaskNotFoundDetail
from services.task import TaskService, get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать задачу",
)
def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return service.create_task(payload)


@router.get(
    "",
    response_model=list[TaskResponse],
    summary="Список задач",
)
def list_tasks(
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return service.list_tasks()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    responses={404: {"model": TaskNotFoundDetail}},
    summary="Получить задачу по ID",
)
def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=TaskNotFoundDetail(task_id=task_id).model_dump(),
        )
    return task
