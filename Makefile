VENV := .venv/bin
PYTHON := $(VENV)/python
ALEMBIC := $(VENV)/alembic
UVICORN := $(VENV)/uvicorn
PYTEST := $(VENV)/pytest

.PHONY: help db-up db-down migrate migrate-check server test

help:
	@echo "ClauseGuard dev commands:"
	@echo "  make db-up         – Start the pgvector Postgres + Redis containers"
	@echo "  make db-down       – Stop all containers"
	@echo "  make migrate       – Run pending Alembic migrations"
	@echo "  make migrate-check – Show current migration revision"
	@echo "  make server        – Start the Uvicorn dev server on port 8000"
	@echo "  make test          – Run the full test + eval suite"

db-up:
	docker compose up -d postgres redis

db-down:
	docker compose down

migrate:
	$(ALEMBIC) upgrade head

migrate-check:
	$(ALEMBIC) current

server:
	$(UVICORN) app.main:app --port 8000

test:
	$(PYTEST) tests/ eval/ -v

worker:
	$(VENV)/celery -A app.workers.celery_app worker --loglevel=info --pool=solo
