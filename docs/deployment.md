# Deployment Guide

## Current Stage

This project currently supports local Docker Compose services for PostgreSQL and
Redis plus Alembic migrations for core backend persistence. No production
deployment infrastructure has been configured.

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm
- uv
- Docker and Docker Compose

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/contentops-agent.git
cd contentops-agent

# 2. Copy environment configuration
cp .env.example .env

# 3. Start PostgreSQL and Redis
make docker-up

# 4. Install all dependencies
make install

# 5. Apply database migrations
make db-upgrade

# 6. Start backend (in one terminal)
make dev-api

# 7. Start frontend (in another terminal)
make dev-web
```

If `make` is unavailable:

```bash
docker compose up -d
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access

- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:3000

## Intended Deployment Architecture (Future)

```
┌─────────────────┐
│   CDN / LB      │
├─────────────────┤
│  Next.js (SSR)  │  Deployed to Vercel or Docker
├─────────────────┤
│  FastAPI (API)  │  Deployed to Cloud Run / ECS / Docker
├─────────────────┤
│  PostgreSQL     │  Managed Cloud SQL / RDS
├─────────────────┤
│  Redis          │  Managed Memorystore / ElastiCache
└─────────────────┘
```

## Environment Variables

See `.env.example` for all required environment variables.

**Never commit `.env` to version control.**

Database settings are environment-driven:

```env
DATABASE_URL=postgresql+psycopg://contentops:contentops_password@localhost:5432/contentops
POSTGRES_USER=contentops
POSTGRES_PASSWORD=contentops_password
POSTGRES_DB=contentops
```

The checked-in values are local-development defaults only. Real deployment
secrets must come from the target environment's secret manager.

## Database Migrations

Apply migrations:

```bash
make db-upgrade
```

Roll back one migration:

```bash
make db-downgrade
```

Create a future migration:

```bash
make db-migrate message="describe change"
```

The current migration creates tables for projects, platform preview results,
mock publish tasks/results, Agent Runs, and Agent Steps. Human Review and
Evaluation persistence are planned follow-up work.

## Not in MVP

- Production deployment configuration (Dockerfiles, Kubernetes manifests).
- CI/CD pipeline for staging and production.
- Database migration automation in CI.
- Real LLM provider integration.
- Real platform publishing.
- Human Review and Evaluation persistence.
- Health check monitoring integration.
- Log aggregation and alerting.
- Secrets management (HashiCorp Vault, AWS Secrets Manager).
- SSL/TLS certificate management.
- Domain and DNS configuration.
