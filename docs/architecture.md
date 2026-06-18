# Architecture Overview

## Current Stage (Phase 3: Deterministic LangGraph Skeleton)

The project is in **Phase 3** with Repository Bootstrap, adapter-driven Preview,
Mock Publish, Agent Trace foundation, and a deterministic LangGraph preview skeleton.
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
- **Agent trace data models and service layer** for in-memory Agent Run / Agent Step records.

No LLM-backed Agent workflow, database models, or real platform publish implementations exist yet.
The current publishing path is mock-only.

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
│  Evaluators         │  Quality evaluation (future)
├─────────────────────┤
│  Telemetry          │  Agent run/step trace records now; logging and metrics later
└─────────────────────┘
```

## Key Design Decisions

- **Monorepo**: Single repository for backend, frontend, and shared packages.
- **Modular backend**: Each layer has a clear responsibility.
- **API-first**: Frontend communicates through a well-defined REST API.
- **Adapter pattern**: Platform-specific logic is isolated behind a common interface.
- **Registry-based platform lookup**: New platforms are added by creating a `PlatformAdapter` implementation and registering it in `apps/api/app/adapters/registry.py`.
- **Deterministic workflow first**: LangGraph is used for a small preview workflow skeleton without LLM calls or provider SDKs.
- **Trace boundary first**: Agent Run and Agent Step records live behind an in-memory repository and `AgentTraceService`; they are not yet connected to the LangGraph skeleton.
- **Human-in-the-loop planned**: Real publishing will require explicit approval before execution, but the approval workflow is not implemented yet.

## LangGraph Workflow Skeleton

The current Agent layer contains a minimal `StateGraph` for content preview:

1. `intake` normalizes source title, source content, and target platform identifiers.
2. `platform_strategy` attaches deterministic strategy labels for requested platforms.
3. `preview_generation` resolves each platform through the PlatformAdapter registry and builds previews.
4. `finish` marks the workflow as completed or failed.

The runner in `apps/api/app/agents/runner.py` hides LangGraph internals from future
service callers. Existing preview and mock publish services remain intact.

## Agent Trace Data Model

The current trace implementation is intentionally small and is not connected to the
LangGraph preview skeleton yet. It provides the data structures and service boundary
needed by future traced workflow nodes:

- `AgentRun` represents one future Agent workflow execution for a project.
- `AgentStep` represents one future node execution within a run.
- Both records track status, input/output snapshots, errors, timestamps, and latency.
- `AgentStep.tool_calls` can record tool call metadata once tools are introduced.
- `TraceRepository` is in-memory only and will be replaced by database persistence later.

Future trace integration will create one Agent Run per workflow and write one Agent
Step per node. Existing preview generation and Mock Publish are not yet recorded in
trace, but they are expected to become traced steps once orchestration is added.

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
- Evaluation system.
- OpenTelemetry instrumentation.
- Async task queue (Celery / Dramatiq).
- Vector search (Qdrant).
