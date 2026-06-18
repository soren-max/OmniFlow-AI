# ContentOps Agent

**Enterprise AI Agent platform for multi-platform content operations.**

ContentOps Agent is an enterprise-style AI Agent application for multi-platform content operations, supporting content adaptation, platform-specific preview, mock publishing, and future Agent workflow orchestration.

---

## Project Background

Content creators and enterprise operations teams face a recurring challenge: **one piece of content must fit multiple platforms**, each with different format requirements, stylistic conventions, and audience expectations.

A WeChat Official Account article requires long-form, formal prose with rich text formatting. A Zhihu post demands analytical depth with a clear Q&A structure. A Bilibili video needs a script-style opening, body content, and call-to-action. A Xiaohongshu note favors short, scannable paragraphs with emoji and heavy tagging. A Douyin clip relies on a strong opening hook, conversational tone, and rapid pacing.

Manually adapting content for each platform is time-consuming, error-prone, and hard to scale. **ContentOps Agent** addresses this by providing an adapter-driven platform that automates content adaptation, preview generation, and mock publishing — with a clear path toward full Agent workflow orchestration.

---

## Current Stage Capabilities

```
- Multi-platform content preview  ✅
- Five platform adapters          ✅
- Adapter registry                ✅
- Mock publish                    ✅
- Rule-based Evaluation Report    ✅
- LangGraph workflow skeleton     ✅
- Agent Run / Step trace records  ✅
- PostgreSQL persistence          ✅
- FastAPI backend                 ✅
- Next.js frontend                ✅
- Enterprise repository standards ✅
- AGENTS.md for AI coding workflow ✅
- CI / PR workflow                ✅
```

### Supported Platforms

| Platform | Identifier | Adapter | Style |
|----------|-----------|---------|-------|
| WeChat Official Accounts | `wechat` | `WeChatAdapter` | Long-form, formal, rich text |
| Zhihu | `zhihu` | `ZhihuAdapter` | Analytical, structured, Q&A |
| Bilibili | `bilibili` | `BilibiliAdapter` | Video script, CTA, tags |
| Xiaohongshu (RED) | `xiaohongshu` | `XiaohongshuAdapter` | Short-form, emoji, tags |
| Douyin | `douyin` | `DouyinAdapter` | Short-video script, hooks |

All adapters implement the same `PlatformAdapter` abstract interface — adding a new platform means adding one adapter class.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                             │
│  ContentEditor → PlatformSelector → PreviewCards → Publish      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (NEXT_PUBLIC_API_BASE_URL)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                              │
│                                                                 │
│  POST /api/projects                                             │
│    → ContentProjectService.create_project()                     │
│    → ProjectRepository → SQLAlchemy → PostgreSQL                 │
│                                                                 │
│  POST /api/projects/{id}/preview                                │
│    → ContentProjectService.generate_previews()                  │
│    → PlatformAdapterRegistry.get_adapter(platform)              │
│    → adapter.transform_content() → validate → build_preview()   │
│                                                                 │
│  POST /api/projects/{id}/publish                                │
│    → ContentProjectService.publish_project()                    │
│    → adapter.mock_publish()                                     │
│                                                                 │
│  POST /api/projects/{id}/agent-preview                          │
│    → LangGraph deterministic preview workflow                   │
│    → PlatformAdapterRegistry.get_adapter(platform)              │
│    → TraceService records Agent Run + Agent Step records         │
│                                                                 │
│  GET /api/runs/{run_id} and /api/runs/{run_id}/steps             │
│    → TraceService reads PostgreSQL workflow trace records        │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
       PlatformAdapter Registry          PostgreSQL / Redis
       (wechat, zhihu, bilibili,         (persistence + local services)
        xiaohongshu, douyin)
```

### Current Workflow

```
Create project → Select platforms → Generate previews → Mock publish
     ▲                                       │
     └────── (view results, then publish) ────┘
```

### LangGraph Preview Skeleton

The backend includes a minimal LangGraph workflow for experimental preview generation:
intake → platform strategy → preview generation → finish. The workflow is deterministic,
does not call a real LLM, and still uses `PlatformAdapter` as the platform adaptation
boundary. Each workflow execution creates a PostgreSQL-backed Agent Run record, and each
node writes an Agent Step record with `running`, `completed`, or `failed` status,
input/output snapshots, latency, and errors.

### Agent Trace Foundation

The backend includes AgentRun and AgentStep data models plus a database-backed
`TraceService` centralized in `apps/api/app/telemetry/`. The LangGraph preview
skeleton records node execution traces for the experimental `agent-preview` path.
Projects, platform preview results, mock publish results, Agent Runs, and Agent
Steps are persisted through SQLAlchemy and Alembic-managed PostgreSQL tables.
Rule-based Evaluation Reports are available for generated previews. Real
publishing, Human Review, and LLM-based evaluation remain future work.

### Evaluation Report

The backend includes a deterministic rule-based evaluator for generated
previews. It scores `format_score`, `style_score`, `consistency_score`,
`compliance_score`, `completeness_score`, and `overall_score`, then surfaces
issues and suggestions per platform. This is not LLM-as-judge and does not call
any model provider.

---

## API Examples

### Create a project

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Trends in 2025",
    "source_text": "Artificial intelligence continues to evolve...",
    "source_url": "https://example.com/article"
  }'
```

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4e5f6",
    "title": "AI Trends in 2025",
    "source_text": "Artificial intelligence continues to evolve...",
    "source_url": "https://example.com/article",
    "status": "created",
    "created_at": "2025-01-01T00:00:00Z",
    "previews": []
  }
}
```

### Generate platform previews

```bash
curl -X POST http://localhost:8000/api/projects/a1b2c3d4e5f6/preview \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"]
  }'
```

```json
{
  "success": true,
  "data": {
    "project_id": "a1b2c3d4e5f6",
    "project_title": "AI Trends in 2025",
    "previews": [
      {
        "platform": "wechat",
        "platform_display_name": "WeChat Official Accounts",
        "title": "AI Trends in 2025",
        "content": "...",
        "rendered_html": "<section class=\"wechat-article\">...",
        "word_count": 1250,
        "estimated_read_time_min": 5,
        "warnings": ["Cover image is recommended for WeChat articles"]
      }
    ],
    "generated_at": "2025-01-01T00:00:00Z"
  }
}
```

### Mock publish

```bash
curl -X POST http://localhost:8000/api/projects/a1b2c3d4e5f6/publish \
  -H "Content-Type: application/json" \
  -d '{
    "target_platforms": ["wechat", "douyin"],
    "mode": "mock"
  }'
```

```json
{
  "success": true,
  "data": {
    "project_id": "a1b2c3d4e5f6",
    "mode": "mock",
    "results": [
      {
        "platform": "wechat",
        "platform_display_name": "WeChat Official Accounts",
        "status": "success",
        "mock_url": "https://mp.weixin.qq.com/s/mock-a1b2c3d4e5f6",
        "message": "Mock published to WeChat Official Accounts successfully."
      },
      {
        "platform": "douyin",
        "platform_display_name": "Douyin",
        "status": "success",
        "mock_url": "mock://douyin/post/mock-a1b2c3d4e5f6",
        "message": "Mock published to Douyin successfully."
      }
    ],
    "published_at": "2025-01-01T00:00:00Z"
  }
}
```

### Agent preview with trace

```bash
curl -X POST http://localhost:8000/api/projects/a1b2c3d4e5f6/agent-preview \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"]
  }'
```

The response includes workflow state and `run_id`. Use that id to inspect the
trace:

```bash
curl http://localhost:8000/api/runs/{run_id}
curl http://localhost:8000/api/runs/{run_id}/steps
```

### Health check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "service": "contentops-api"
}
```

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) — Python package manager
- [pnpm](https://pnpm.io/) — Node.js package manager
- Docker & Docker Compose

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/contentops-agent.git
cd contentops-agent

# 2. Copy environment configuration
cp .env.example .env

# 3. Start PostgreSQL and Redis (Docker)
make docker-up

# 4. Install all dependencies
make install

# 5. Start the backend API (terminal 1)
make dev-api

# 6. Start the frontend (terminal 2)
make dev-web
```

### Access

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all Python + Node.js dependencies |
| `make dev-api` | Start FastAPI backend with hot reload |
| `make dev-web` | Start Next.js frontend with hot reload |
| `make lint` | Run ruff (Python) + eslint (frontend) |
| `make format` | Run ruff format + prettier |
| `make typecheck` | Run mypy (Python) + tsc (frontend) |
| `make test` | Run pytest (Python) + frontend tests |
| `make db-migrate` | Create an Alembic migration (`message='...'`) |
| `make db-upgrade` | Apply Alembic migrations |
| `make db-downgrade` | Roll back one Alembic migration |
| `make docker-up` | Start PostgreSQL + Redis |
| `make docker-down` | Stop all Docker services |

### Running Tests

```bash
# Run all backend tests
make test

# Or directly
uv run pytest apps/api/tests/ -v --tb=short
```

### Running Lint & Type Checks

```bash
# Python linting
uv run ruff check apps/api/

# Python type checking
uv run mypy apps/api/ --config-file pyproject.toml

# Frontend lint
cd apps/web && pnpm lint

# Frontend type check
cd apps/web && pnpm typecheck
```

---

## Engineering Standards

### AGENTS.md

The root [`AGENTS.md`](./AGENTS.md) defines the repository's highest development rules. Every AI coding tool and developer must read and follow it before making changes. It covers:

- Project goal and target role alignment.
- Repository structure and module responsibilities.
- Development rules (smallest correct change, no secrets, test-first).
- Git workflow (GitHub Flow, branch naming, commit convention).
- Coding standards (Python 3.12, type hints, Pydantic, FastAPI route thinness).
- Agent design principles (deterministic nodes, clear IO schemas, human approval).
- Platform adapter rules (common interface, no platform logic in agents).
- Testing rules (every route tested, httpx AsyncClient, no skipped tests).
- Current stage bootstrap rules and future scope.

### Pull Request Workflow

This project uses **GitHub Flow** with PR-based development.

```
1. Create a feature branch from main
2. Make small, focused commits
3. Run make lint, make typecheck, make test
4. Open a Pull Request
5. CI runs automatically (ruff → mypy → pytest / pnpm build)
6. Get review approval
7. Squash-merge to main
```

See [docs/pr-workflow.md](docs/pr-workflow.md) for the full PR workflow.

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(api): add health check endpoint
fix(adapter): handle empty platform content
docs(readme): add local development guide
test(api): add project creation tests
chore(repo): initialize monorepo structure
```

### CI Pipeline

| Workflow | Tools |
|----------|-------|
| Backend CI (.github/workflows/backend.yml) | ruff check → mypy → pytest |
| Frontend CI (.github/workflows/frontend.yml) | pnpm lint → tsc typecheck → pnpm test |

---

## Current Limitations

The following features are **explicitly out of scope** for the current stage:

| Limitation | Status |
|------------|--------|
| Real platform publishing | ❌ Not implemented. `adapter.publish()` raises `NotImplementedError`. |
| LangGraph workflow orchestration | ✅ Minimal deterministic preview skeleton only; no LLM calls. |
| Agent Run Trace | ✅ PostgreSQL-backed Agent Run and Agent Step records for the LangGraph preview skeleton. |
| Human Review workflow | ❌ No approval/rejection flow before publish. |
| Evaluation Reports | ✅ Rule-based quality scoring for generated previews. Not LLM-as-judge. |
| Authentication / Authorization | ❌ No user system, API keys, or session management. |
| Database persistence | ✅ Projects, previews, mock publish results, Agent Runs, and Agent Steps are persisted in PostgreSQL. |
| Review persistence | 🔜 Planned with Human Review. |
| Frontend tests | ❌ `pnpm test` is a placeholder — no Vitest/Jest configured. |

---

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Repository bootstrap and adapter-driven preview | ✅ **Done** |
| **Phase 2** | Mock Publish and API schema stabilization | ✅ **Done** |
| **Phase 3** | LangGraph preview skeleton and PostgreSQL-backed Agent Run Trace | ✅ **In progress** |
| **Phase 4** | Human Review and traced workflow integration | 🔜 Planned |
| **Phase 5** | Evaluation and observability | 🔜 Planned |
| **Phase 6** | Real publishing integrations with explicit approval | 🔜 Planned |

---

## Why This Project Matters for AI Agent Engineering

ContentOps Agent is designed as a **demonstration-quality project** for AI Agent application engineering. It showcases:

### Agent-Ready Architecture

The codebase is structured for Agent workflow integration from day one:

- `agents/` module contains a deterministic LangGraph preview skeleton; full AI orchestration is future work.
- `adapters/` module provides the tool-calling interface that agents will invoke.
- `schemas/` holds Pydantic models that define the input/output contract for every Agent node.
- `services/` contains business logic that can be called by both API routes and Agent nodes.
- `telemetry/` contains PostgreSQL-backed Agent Run and Agent Step records; `evaluators/` remains reserved for quality scoring.

### Tool / Adapter Abstraction

The `PlatformAdapter` abstract base class demonstrates the **tool abstraction pattern** central to AI Agent design:

> Agents do not call platform APIs directly. They call tools. Tools abstract away platform-specific complexity behind a clean interface.

This repo shows how to design a tool interface (`PlatformAdapter`), register tools (`registry.py`), and execute them in a service layer — all without hardcoding platform names in business logic.

### Human-in-the-Loop Preparation

The API design anticipates human approval:

- `POST /api/projects/{id}/publish` requires an explicit `mode` parameter. Real publishing (`mode: "real"`) is structurally possible but currently raises `NotImplementedError` — enforced until human review is implemented.
- Preview responses include validation warnings that inform review decisions.

### Evaluation-Ready Design

The `evals/` directory at the project root and the `evaluators/` backend module are reserved for quality metrics. The data model (`PublishResult`, `ValidationResult`) already carries the fields that evaluation scoring will consume.

### Enterprise PR Workflow

- `AGENTS.md` enforces coding standards, testing rules, and branch policies.
- GitHub Actions enforce ruff, mypy, and pytest on every PR.
- PR templates include a checklist linked to `AGENTS.md`.
- Conventional Commits produce a clean changelog.

### AI Coding Workflow Using AGENTS.md

`AGENTS.md` acts as a **prompt-level constraint** for AI coding tools. It defines:

- What the current stage allows and forbids.
- The expected repository structure and module responsibilities.
- Coding standards, testing rules, and commit conventions.
- Future scope — preventing premature expansion beyond the current LangGraph skeleton into real publishing, production LLM calls, or evaluation.

This document serves as the single source of truth that aligns human developers and AI assistants on the same development rules.

---

## Project Structure

```
contentops-agent/
├── AGENTS.md                   # Development rules (MUST READ)
├── README.md                   # This file
├── .env.example                # Environment variables template
├── docker-compose.yml          # PostgreSQL + Redis
├── Makefile                    # Dev commands
├── pyproject.toml              # Python dependencies & tooling config
├── package.json                # Node.js workspace root
├── pnpm-workspace.yaml         # pnpm workspace config
│
├── apps/
│   ├── api/                    # FastAPI backend
│   └── web/                    # Next.js frontend
│
├── packages/
│   ├── shared/                 # Shared TypeScript types
│   └── prompts/                # Agent prompt templates (future)
│
├── docs/                       # Architecture & design docs
├── evals/                      # Evaluation datasets & reports (future)
├── scripts/                    # Development scripts
└── .github/                    # PR templates, CI workflows, issue templates
```

---

## Security

- **Never commit `.env` files.**
- Never hardcode API keys, tokens, or secrets.
- All secrets must be loaded from environment variables.
- Use `.env.example` as a template — never as a working config.

See [AGENTS.md](AGENTS.md) for full development rules.

---

## License

MIT
