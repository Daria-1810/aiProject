import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import task as crud
from app.db.session import get_db
from app.schemas.task import ErrorDetail, Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

NOT_FOUND_RESPONSE = {status.HTTP_404_NOT_FOUND: {"model": ErrorDetail, "description": "Task not found"}}


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db)) -> Task:
    return crud.create_task(db, data)


@router.get("", response_model=list[Task])
def list_tasks(
    due_after: datetime | None = None,
    due_before: datetime | None = None,
    sort: Literal["due_at"] | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
) -> list[Task]:
    return crud.list_tasks(db, due_after=due_after, due_before=due_before, sort=sort, order=order)


@router.get("/{task_id}", response_model=Task, responses=NOT_FOUND_RESPONSE)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> Task:
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=Task, responses=NOT_FOUND_RESPONSE)
def update_task(task_id: uuid.UUID, data: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return crud.update_task(db, task, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND_RESPONSE)
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    crud.delete_task(db, task)
