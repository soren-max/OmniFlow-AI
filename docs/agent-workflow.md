# Agent Workflow

## Current Stage (Phase 3: Deterministic LangGraph Skeleton)

LangGraph is now introduced as a minimal deterministic workflow skeleton.
It does not call an LLM, external model provider, real platform API, Human Review,
or Evaluation service.

The current skeleton includes:

1. `intake_node` for deterministic input cleanup and validation.
2. `platform_strategy_node` for simple platform strategy labels.
3. `preview_generation_node` for adapter-backed preview generation.
4. `finish_node` for marking the workflow complete.

Today the product still uses the existing `POST /api/projects/{id}/preview` API for
the main preview path. The experimental `POST /api/projects/{id}/agent-preview`
endpoint calls the LangGraph runner and returns workflow state for validation.

The PlatformAdapter registry remains the core platform abstraction. The workflow
preview node resolves adapters through the registry and does not hardcode
platform-specific adapter behavior.

Each `agent-preview` execution now creates a PostgreSQL-backed Agent Run trace. Each
LangGraph node is wrapped by the telemetry trace layer and writes an Agent Step
with status, input/output snapshots, latency, and errors. Trace schemas,
repository access, and service transitions are centralized in
`apps/api/app/telemetry/`. The web demo can display the generated `run_id` and a
basic Trace Viewer for the run and step records. Human Review is currently an
API-level gate before Mock Publish. Evaluation is currently rule-based and
service-level; real publishing remains future work.

## Current Trace Flow

```
run_content_preview_workflow()
        │
        ▼
TraceService.create_run(status="running")
        │
        ▼
intake → platform_strategy → preview_generation → finish
  │              │                    │              │
  └──── TraceService records one Agent Step per node ┘
        │
        ▼
TraceService.finish_run(...) or TraceService.fail_run(...)
```

Trace status values are standardized as `running`, `completed`, and `failed`.
The runner adds `run_id` to workflow state. API callers can inspect records with:

- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/steps`

The Next.js demo flow surfaces the `run_id` after preview generation and loads
these endpoints on demand in a basic Trace Viewer. The viewer is intended for
interview and local demo visibility, not full production observability.

Preview and Mock Publish will later be incorporated into the same trace history
when the workflow expands beyond the deterministic preview skeleton.

## Current Human Review Gate

The current implementation adds Human Review as a project-level API gate:

- Preview generation sets project status to `pending`.
- `POST /api/projects/{id}/review/approve` sets status to `approved`.
- `POST /api/projects/{id}/review/reject` sets status to `rejected`.
- `POST /api/projects/{id}/publish` only allows Mock Publish when status is
  `approved`.

This is intentionally not a full LangGraph human-in-the-loop node yet. A future
workflow PR can move the same approval boundary into the Agent graph.

## Intended Workflow (Future)

When the full Agent workflow is introduced, it will follow this sequence:

```
Source Content / Idea
        │
        ▼
┌──────────────────────┐
│  Content Intake      │  Parse, normalize, extract metadata
├──────────────────────┤
│  Platform Strategy   │  Select target platforms, define style
├──────────────────────┤
│  Content Rewrite     │  Adapt content per platform style
├──────────────────────┤
│  Title & Hook Gen    │  Generate platform-specific titles
├──────────────────────┤
│  Compliance Review   │  Check content against platform rules
├──────────────────────┤
│  Format Adaptation   │  Convert to platform format (HTML, Markdown, etc.)
├──────────────────────┤
│  Preview Generation  │  Build visual previews
├──────────────────────┤
│  Human Approval      │  Require user approval before publishing
├──────────────────────┤
│  Publish Execution   │  Mock or real publish via adapters
├──────────────────────┤
│  Evaluation          │  Score quality, log results, record trace
└──────────────────────┘
```

## Agent Node Responsibilities (Future)

| Node | Input | Output |
|------|-------|--------|
| Content Intake | Raw text / URL / idea | Normalized content with metadata |
| Platform Strategy | Content + target platforms | Strategy per platform |
| Content Rewrite | Content + strategy | Platform-adapted content |
| Title & Hook Gen | Adapted content | Titles, hooks, tags |
| Compliance Review | Content + platform rules | Pass / Fail with reasons |
| Format Adaptation | Content + platform format | Platform-ready content |
| Preview Generation | Formatted content | Preview data |
| Human Approval | All previews | Approved / Rejected |
| Publish Execution | Approved content | Publish result |
| Evaluation | Full run data | Quality scores, report |

## Key Principles (Future)

- Each node is deterministic where possible.
- Each node has a clear input/output schema (Pydantic).
- No single node should handle multiple responsibilities.
- Every Agent run must be recorded (steps, tool calls, latency, errors). The
  current skeleton records run/step status, snapshots, latency, and errors in
  PostgreSQL; token usage is still future work because no LLM is called.
- Human approval is mandatory before Mock Publish in the current API gate. Full
  graph-native Human Review is future work.

## Not in MVP

The full Agent workflow is still out of scope. The current implementation includes
only the deterministic LangGraph preview skeleton plus PostgreSQL-backed trace
records and a basic web Trace Viewer. Real LLM calls, Prompt Engineering, RAG,
full graph-native Human Review, LLM-as-judge Evaluation, and real publishing are
not implemented.
