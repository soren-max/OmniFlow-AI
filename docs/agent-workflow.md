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

The repository now includes foundational Trace data models and service methods:

- Agent Run records describe one future workflow execution.
- Agent Step records describe one future node execution.
- The trace repository is in-memory only.
- The trace service supports create, finish, fail, and list operations.

These trace records are not connected to the LangGraph skeleton yet. They define the
execution trace boundary that future workflow nodes will use.

The PlatformAdapter registry remains the core platform abstraction. The workflow
preview node resolves adapters through the registry and does not hardcode
platform-specific adapter behavior.

Preview and Mock Publish will later be connected to Agent Run Trace. Human Review
and Evaluation remain future work.

## Trace Recording Plan

When trace integration is added, each workflow invocation will create one Agent Run.
Each LangGraph node will create one Agent Step when it starts, then finish or fail
that step with output snapshots, tool calls, latency, and error details.

Preview generation and Mock Publish are still direct service calls today. In a later
workflow PR, they should be wrapped as traced nodes so preview and mock publish results
are captured inside Agent Step records.

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
- Every Agent run must be recorded (steps, tool calls, latency, errors).
- Human approval is mandatory before any publish action.

## Not in MVP

The full Agent workflow is still out of scope. This PR adds only the deterministic
LangGraph preview skeleton. Real LLM calls, Prompt Engineering, RAG, Human Review,
Evaluation, and real publishing are not implemented.
