from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers.tasks import router as tasks_router
from app.db.base import Base
from app.db.session import engine
from app.models import task as _task_model  # noqa: F401  ensures model is registered


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="TODO REST API", version="1.0.0", lifespan=lifespan)
app.include_router(tasks_router, prefix="/api/v1")
