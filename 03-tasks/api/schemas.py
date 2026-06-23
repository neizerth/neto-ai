from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Название задачи",
        examples=["Настроить CI/CD"],
    )
    description: str | None = Field(
        default=None,
        description="Описание задачи",
        examples=["Добавить GitHub Actions для автотестов"],
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="Приоритет от 1 (низкий) до 5 (высокий)",
        examples=[3],
    )


class TaskResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "title": "Настроить CI/CD",
                    "description": "Добавить GitHub Actions для автотестов",
                    "priority": 3,
                    "created_at": "2026-06-23T12:00:00",
                }
            ]
        }
    )

    id: int = Field(..., description="Уникальный идентификатор задачи")
    title: str = Field(..., min_length=3, max_length=100)
    description: str | None = None
    priority: int = Field(..., ge=1, le=5)
    created_at: datetime = Field(..., description="Дата и время создания (ISO 8601)")


class TaskNotFoundDetail(BaseModel):
    detail: str = "Task not found"
    task_id: int
