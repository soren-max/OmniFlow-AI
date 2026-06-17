# Deployment Guide

## Current Stage (Phase 1-2)

This project is currently in **Phase 1-2** (Repository Bootstrap + Mock Publish). No production deployment infrastructure has been configured.

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

# 5. Start backend (in one terminal)
make dev-api

# 6. Start frontend (in another terminal)
make dev-web
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

## Not in MVP

- Production deployment configuration (Dockerfiles, Kubernetes manifests).
- CI/CD pipeline for staging and production.
- Database migration automation in CI.
- Health check monitoring integration.
- Log aggregation and alerting.
- Secrets management (HashiCorp Vault, AWS Secrets Manager).
- SSL/TLS certificate management.
- Domain and DNS configuration.
