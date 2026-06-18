.PHONY: install dev-api dev-web lint format typecheck test db-migrate db-upgrade db-downgrade docker-up docker-down

# Install all dependencies
install:
	uv sync --dev
	pnpm install

# Start FastAPI backend
dev-api:
	uv run uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Next.js frontend
dev-web:
	pnpm --filter @contentops/web dev

# Run all linting
lint:
	uv run ruff check apps/api/
	pnpm --filter @contentops/web lint

# Format all code
format:
	uv run ruff format apps/api/
	pnpm --filter @contentops/web format

# Run type checking
typecheck:
	uv run mypy apps/api/ --config-file pyproject.toml
	pnpm --filter @contentops/web typecheck

# Run all tests
test:
	uv run pytest apps/api/tests/ -v --tb=short
	pnpm --filter @contentops/web test

# Create a new Alembic migration after model changes
db-migrate:
	uv run alembic revision --autogenerate -m "$(message)"

# Apply database migrations
db-upgrade:
	uv run alembic upgrade head

# Roll back one database migration
db-downgrade:
	uv run alembic downgrade -1

# Start Docker services (PostgreSQL + Redis)
docker-up:
	docker compose up -d

# Stop Docker services
docker-down:
	docker compose down

# Show help
help:
	@echo "ContentOps Agent - Development Commands"
	@echo "---------------------------------------"
	@echo "install       Install all dependencies (Python + Node)"
	@echo "dev-api       Start FastAPI backend at localhost:8000"
	@echo "dev-web       Start Next.js frontend at localhost:3000"
	@echo "lint          Run ruff (Python) and eslint (Next.js)"
	@echo "format        Run ruff format (Python) and prettier (Next.js)"
	@echo "typecheck     Run mypy (Python) and tsc (Next.js)"
	@echo "test          Run pytest (Python) and vitest/jest (Next.js)"
	@echo "db-migrate    Create an Alembic migration (message='...')"
	@echo "db-upgrade    Apply Alembic migrations"
	@echo "db-downgrade  Roll back one Alembic migration"
	@echo "docker-up     Start PostgreSQL and Redis via Docker"
	@echo "docker-down   Stop Docker services"
