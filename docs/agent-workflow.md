# Agent Workflow

## Current Stage (Phase 1-2: Adapter-Driven Preview + Mock Publish)

**Do NOT introduce LangGraph in this stage.**

The repository is currently in Phase 1-2. LangGraph will be introduced in a later stage when:

1. The basic FastAPI application is stable. ✅
2. Database models and migrations are in place.
3. The **PlatformAdapter abstract interface** is designed and reviewed. ✅
4. **Mock platform adapter implementations** exist for all 5 platforms. ✅
5. The evaluation framework is designed.

Today the product is in an adapter-driven preview stage. `POST /api/projects/{id}/preview`
uses the PlatformAdapter registry to produce mock previews for WeChat, Zhihu,
Bilibili, Xiaohongshu, and Douyin. No LangGraph workflow, real publishing, or
Agent trace persistence is implemented yet.

LangGraph should be introduced after the API contract, PlatformAdapter behavior,
project data model, Agent Run / Agent Step records, and human review status flow
are stable.

## Intended Workflow (Future)

When LangGraph is introduced, the Agent workflow will follow this sequence:

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

This entire workflow is out of scope for the bootstrap stage.
