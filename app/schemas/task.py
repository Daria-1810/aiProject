import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskStatus

__all__ = ["TaskStatus", "TaskCreate", "TaskUpdate", "Task", "ErrorDetail"]


class ErrorDetail(BaseModel):
    detail: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("due_at")
    @classmethod
    def _due_at_not_in_past(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        v_aware = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)
        if v_aware < datetime.now(timezone.utc):
            raise ValueError("due_at must not be earlier than the current moment")
        return v


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_not_null_or_blank(cls, v: str | None) -> str:
        if v is None:
            raise ValueError("title must not be null")
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("status")
    @classmethod
    def _status_not_null(cls, v: TaskStatus | None) -> TaskStatus:
        if v is None:
            raise ValueError("status must not be null")
        return v

    @field_validator("due_at")
    @classmethod
    def _due_at_not_in_past(cls, v: datetime | None) -> datetime | None:
        # unlike title/status, null is allowed here — it clears the due date
        if v is None:
            return v
        v_aware = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)
        if v_aware < datetime.now(timezone.utc):
            raise ValueError("due_at must not be earlier than the current moment")
        return v


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None = None
    status: TaskStatus
    due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
