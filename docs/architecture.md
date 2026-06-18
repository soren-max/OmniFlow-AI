# Architecture Overview

## Current Stage (Phase 3: Deterministic LangGraph Skeleton)

The project is in **Phase 3** with Repository Bootstrap, adapter-driven Preview,
Mock Publish, rule-based Evaluation Report, Agent Trace foundation, and a
deterministic LangGraph preview skeleton.
The adapter-driven preview and mock publish pipeline is operational:

- FastAPI backend with a health check endpoint.
- Next.js frontend with content input and multi-platform preview UI.
- Docker Compose for PostgreSQL and Redis.
- CI workflows for both backend and frontend.
- **PlatformAdapter abstract interface** in `apps/api/app/adapters/`.
- **Mock adapters** for all 5 target platforms (WeChat, Zhihu, Bilibili, Xiaohongshu, Douyin).
- **Adapter registry** for platform → class resolution.
- Shared adapter data types: Platform, PlatformContent, ValidationResult, PublishResult, etc.
- **Deterministic LangGraph preview workflow skeleton** in `apps/api/app/agents/`.
- **Rule-based evaluation reports** in `apps/api/app/evaluators/`.
- **PostgreSQL-backed Agent Run and Agent Step trace records** in `apps/api/app/telemetry/`.
- **SQLAlchemy repositories and Alembic migrations** for projects, platform preview
  results, mock publish results, Evaluation Reports, Agent Runs, and Agent Steps.

No LLM-backed Agent workflow, Human Review workflow, LLM-as-judge evaluation, or
real platform publish implementations exist yet. The current publishing path is
mock-only.

## Intended Architecture (Future)

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                    │
│  app/page.tsx │ components/ │ lib/ │ hooks/ │ types/   │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP / WebSocket
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                      │
│  api/ → services/ → repositories/ → SQLAlchemy → PostgreSQL│
│  agents/ (LangGraph) │ adapters/ │ evaluators/           │
│  telemetry/ │ core/ │ schemas/                           │
└──────┬───────────────────────┬───────────────────────────┘
       │                       │
       ▼                       ▼
   Redis (Cache)         PostgreSQL (Persistence)
```

## Layer Responsibilities

```
┌─────────────────────┐
│    API Routes       │  Thin layer: validation, routing, response
├─────────────────────┤
│    Services         │  Business logic, orchestrations
├─────────────────────┤
│  Repositories       │  Database access, queries
├─────────────────────┤
│  SQLAlchemy Models  │  ORM mappings
├─────────────────────┤
│  Agents (LangGraph) │  Deterministic preview skeleton now; AI orchestration later
├─────────────────────┤
│  Adapters           │  Platform-specific publishing (mock adapters + registry done)
├─────────────────────┤
│  Evaluators         │  Rule-based quality evaluation now; LLM-as-judge later
├─────────────────────┤
│  Telemetry          │  PostgreSQL Agent Run and Agent Step traces now; metrics later
└─────────────────────┘
```

## Key Design Decisions

- **Monorepo**: Single repository for backend, frontend, and shared packages.
- **Modular backend**: Each layer has a clear responsibility.
- **API-first**: Frontend communicates through a well-defined REST API.
- **Adapter pattern**: Platform-specific logic is isolated behind a common interface.
- **Registry-based platform lookup**: New platforms are added by creating a `PlatformAdapter` implementation and registering it in `apps/api/app/adapters/registry.py`.
- **Deterministic workflow first**: LangGraph is used for a small preview workflow skeleton without LLM calls or provider SDKs.
- **Centralized telemetry trace service**: Agent Run and Agent Step schemas,
  repository access, and lifecycle transitions live under `apps/api/app/telemetry/`;
  workflow nodes do not persist trace records directly.
- **Repository-backed persistence**: services call repositories that write core records
  through SQLAlchemy models; routes stay thin and do not perform database queries.
- **Rule-based evaluation first**: evaluation scores are deterministic checks over
  generated previews and adapter validation output, not LLM-as-judge.
- **Human-in-the-loop planned**: Real publishing will require explicit approval before execution, but the approval workflow is not implemented yet.

## LangGraph Workflow Skeleton

The current Agent layer contains a minimal `StateGraph` for content preview:

1. `intake` normalizes source title, source content, and target platform identifiers.
2. `platform_strategy` attaches deterministic strategy labels for requested platforms.
3. `preview_generation` resolves each platform through the PlatformAdapter registry and builds previews.
4. `finish` marks the workflow as completed or failed.

The runner in `apps/api/app/agents/runner.py` hides LangGraph internals from future
service callers. Existing preview and mock publish services remain intact.

## Agent Trace Recording

The current LangGraph preview runner creates one Agent Run per workflow execution.
Each wrapped node creates one Agent Step and records:

- `running`, `completed`, or `failed` status.
- Input and output snapshots.
- Error messages when a node or run fails.
- Step latency and total run latency.
- Tool call metadata placeholder fields.

Trace status values are standardized as `running`, `completed`, and `failed`.
The canonical implementation is `apps/api/app/telemetry/`; older service/schema
paths should not be used for new workflow or API code.

Trace records are stored in PostgreSQL through the trace repository. They are available
through `GET /api/runs/{run_id}` and `GET /api/runs/{run_id}/steps`. The
`POST /api/projects/{id}/agent-preview` response includes `run_id` so callers can
inspect the workflow trace.

Projects, platform preview results, mock publish results, Evaluation Reports,
Agent Runs, and Agent Steps are covered by the current PostgreSQL persistence
layer. ReviewRecord persistence is planned for later Human Review work.

## Rule-Based Evaluation

`apps/api/app/evaluators/rule_based.py` scores saved previews across:

- `format_score`
- `style_score`
- `consistency_score`
- `compliance_score`
- `completeness_score`
- `overall_score`

Reports also include platform-level issues and suggestions. This baseline is
deterministic and does not call an LLM.

## PlatformAdapter Flow

Current preview and mock publish execution are adapter-driven:

1. The API receives target platform identifiers such as `wechat` or `douyin`.
2. The service resolves each identifier to the `Platform` enum.
3. The adapter registry returns the matching adapter.
4. For preview, the adapter transforms content, validates it, and builds a mock preview.
5. For mock publish, the service calls `adapter.mock_publish` and returns simulated results.

Adding a platform should stay localized to the adapter layer: add a concrete adapter, add the platform enum value, register the adapter, and update tests and UI platform options. Business services should continue resolving adapters through the registry instead of branching on platform names.

Real publishing is a future extension of the same PlatformAdapter boundary. It must
not call external platform APIs until Human Review, explicit authorization, secure
credential handling, and trace logging are in place.

## Not in MVP

- LLM-backed LangGraph agent orchestration.
- **Real platform API integration** (mock adapters and mock publish are done).
- Human Review workflow and ReviewRecord persistence.
- LLM-as-judge evaluation.
- OpenTelemetry instrumentation.
- Async task queue (Celery / Dramatiq).
- Vector search (Qdrant).
