import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _next_timestamp(previous: datetime) -> datetime:
    # OS clock resolution (~15.6ms on Windows) can repeat a value between two calls; force it forward if so.
    now = _utcnow()
    now_aware = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
    previous_aware = previous if previous.tzinfo is not None else previous.replace(tzinfo=timezone.utc)
    if now_aware <= previous_aware:
        now = previous_aware + timedelta(microseconds=1)
    return now


def create_task(db: Session, data: TaskCreate) -> Task:
    now = _utcnow()
    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        due_at=data.due_at,
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    due_after: datetime | None = None,
    due_before: datetime | None = None,
    sort: str | None = None,
    order: str = "asc",
) -> list[Task]:
    stmt = select(Task)
    if due_after is not None:
        stmt = stmt.where(Task.due_at >= due_after)
    if due_before is not None:
        stmt = stmt.where(Task.due_at <= due_before)
    if sort == "due_at":
        stmt = stmt.order_by(Task.due_at.desc() if order == "desc" else Task.due_at.asc())
    else:
        stmt = stmt.order_by(Task.created_at.asc())
    return list(db.scalars(stmt).all())


def get_task(db: Session, task_id: uuid.UUID) -> Task | None:
    return db.get(Task, task_id)


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)
    task.updated_at = _next_timestamp(task.updated_at)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
