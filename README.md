# TODO REST API

Single-user REST API для управления задачами. Реализовано на FastAPI + SQLAlchemy, хранилище — SQLite.

Требования и контракт: [docs/spec.md](docs/spec.md), [docs/openapi.yaml](docs/openapi.yaml).

## Установка

    pip install -e ".[dev]"

## Запуск

    uvicorn app.main:app --reload

Документация API: http://127.0.0.1:8000/docs

## Тесты

    pytest
