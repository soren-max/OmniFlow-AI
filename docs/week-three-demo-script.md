# Week Three Demo Script

## Purpose

This script is for a 5-minute interview or project review demo of ContentOps
Agent. The goal is to show that the project is not only a content preview tool,
but an observable, reviewable, and evaluable Agent workflow platform for
multi-platform content operations.

The demo must stay honest about the current stage:

- No real LLM provider is connected.
- No real platform publishing is implemented.
- No complex authentication system is included.
- No production deployment guarantee is made.
- Mock Publish is only a simulated publishing flow.

## 1. 5-Minute Demo Flow

### 0:00-0:30 — Open README And Position The Project

Open `README.md` and introduce the product:

> ContentOps Agent is an enterprise-style AI Agent application for
> multi-platform content operations. It adapts one source article or idea into
> platform-specific previews, records the Agent workflow trace, requires human
> approval before publishing, and generates a rule-based evaluation report.

Point out the current engineering focus:

- FastAPI backend and Next.js frontend.
- PlatformAdapter plugin architecture.
- Deterministic LangGraph workflow skeleton.
- Agent Run / Step Trace.
- Human Review gate before Mock Publish.
- Rule-based Evaluation.
- CI and PR-based development workflow.

### 0:30-1:00 — Start Backend And Frontend

Start dependencies and services from the repository root:

```bash
docker compose up -d
uv run uvicorn api.app.main:app --reload --app-dir apps/api
pnpm dev
```

Open the web app in the browser and keep the backend API docs available if
needed.

### 1:00-1:30 — Create Content Project

In the web UI:

1. Enter a source title.
2. Paste a short article or content idea.
3. Explain that this creates a content project in the backend and persists it
   through the repository/database layer.

### 1:30-2:00 — Select Five Platforms

Select all five supported platforms:

1. WeChat Official Account / 微信公众号
2. Zhihu / 知乎
3. Bilibili / B站
4. Xiaohongshu / 小红书
5. Douyin / 抖音

Explain that platform-specific behavior is isolated behind the PlatformAdapter
Registry instead of being hardcoded into the Agent workflow.

### 2:00-2:40 — Generate Multi-Platform Preview

Click the preview generation button.

Show that the same source content becomes platform-specific preview output:

- Different titles or presentation styles.
- Platform-specific metadata.
- Rendered preview content.
- Validation warnings if present.

Explain that preview generation is adapter-driven and currently deterministic.

### 2:40-3:15 — View Agent Trace Viewer

After preview generation, point to the returned `run_id` and open the Trace
Viewer.

Show:

- Agent Run metadata.
- Workflow status.
- Started and finished timestamps.
- Total latency.
- Agent Step list.
- Node names such as `intake`, `platform_strategy`, `preview_generation`, and
  `finish`.
- Step status, latency, and error messages when present.

Position this as demo-level observability for an Agent workflow, not a full
production tracing platform.

### 3:15-3:45 — Execute Human Review Approve

Show the Human Review section.

Explain:

- New previews require approval before publishing.
- `pending` and `rejected` projects cannot be published.
- Clicking approve moves the project into an approved state.

Click `Approve`.

### 3:45-4:10 — Execute Mock Publish

Click `Mock Publish` after approval.

Show mock publish results and explain:

- This uses the same PlatformAdapter boundary.
- It does not call real platform APIs.
- It demonstrates the safety gate and publish orchestration without external
  credentials.

### 4:10-4:35 — Run Evaluation Report

Run the Evaluation Report.

Show:

- Average score.
- Platform-level scores.
- Issues.
- Suggestions.

Explain that this is deterministic and rule-based, not LLM-as-judge.

### 4:35-5:00 — Current Limits And Roadmap

Close by stating the limits clearly:

- No real LLM calls yet.
- No real platform publishing yet.
- No production auth system yet.
- No production deployment guarantee yet.
- Mock Publish is not real publishing.

Roadmap:

- Add LLM-backed Agent nodes after the deterministic workflow is stable.
- Add graph-native Human Review node.
- Add stronger evaluation and feedback loops.
- Add production-grade observability and deployment only after core workflow
  boundaries are proven.

## 2. Architecture Talk Track

Use this short architecture map while explaining the system:

```text
Next.js Frontend
    |
    v
FastAPI Backend
    |
    +--> Services / Review Gate / Evaluation
    |
    +--> PlatformAdapter Registry
    |       +--> WeChat Adapter
    |       +--> Zhihu Adapter
    |       +--> Bilibili Adapter
    |       +--> Xiaohongshu Adapter
    |       +--> Douyin Adapter
    |
    +--> LangGraph Workflow
    |       +--> TraceService
    |
    +--> Repository Layer
            +--> Database
```

### Next.js Frontend

The frontend provides the demo workflow: content input, platform selection,
preview display, Trace Viewer, Human Review actions, Mock Publish, and Evaluation
Report display.

### FastAPI Backend

FastAPI exposes thin HTTP routes for projects, preview generation, Agent runs,
steps, review actions, publishing, and evaluation. The routes delegate business
logic to services instead of mixing API and domain behavior.

### PlatformAdapter Registry

PlatformAdapter is the core extension point for platform-specific behavior. Each
platform adapter owns its validation, transformation, preview building, and mock
publish behavior.

### LangGraph Workflow

LangGraph currently provides a deterministic preview workflow skeleton. It
orchestrates nodes but does not contain platform-specific publishing logic.

### TraceService

TraceService records Agent Run and Agent Step lifecycle data, including status,
latency, snapshots, and error messages. The Trace Viewer reads this data through
the run and step API endpoints.

### ReviewService / Review Gate

The review gate ensures content must be approved before Mock Publish. In the
current implementation, this is an API/service-level boundary; a later version
can move it into the LangGraph workflow as a human-in-the-loop node.

### EvaluationService

Evaluation is currently rule-based. It scores saved previews across format,
style, consistency, compliance, completeness, and overall quality dimensions.

### Mock Publish

Mock Publish simulates publishing through adapters after approval. It is useful
for demoing orchestration and safety boundaries without real platform APIs.

### Repository / Database Layer

The repository layer persists projects, previews, mock publish results, Agent Run
records, Agent Step records, and evaluation reports. This keeps service logic
separate from database access.

## 3. Agent Workflow Talk Track

Current workflow:

```text
Intake -> Platform Strategy -> Preview Generation -> Finish
```

How to explain it:

- `Intake` normalizes and validates the source title, source content, and target
  platforms.
- `Platform Strategy` assigns deterministic strategy labels for each platform.
- `Preview Generation` calls the PlatformAdapter Registry to build previews.
- `Finish` marks the workflow as completed or failed.

Important boundaries:

- The current workflow is a deterministic skeleton.
- The current workflow does not call a real LLM.
- Platform details stay in adapters, not inside Agent nodes.
- Future nodes can add LLM rewrite, Human Review, Evaluation, feedback, and
  stronger compliance checks.

## 4. Trace Talk Track

Every workflow execution creates one Agent Run.

Each workflow node creates one Agent Step.

The Trace Viewer shows:

- `node_name`
- `status`
- `latency_ms`
- `error_message`

Suggested explanation:

> This is important because Agent applications need observability. When a demo
> fails or a node returns bad output, I can inspect which node ran, whether it
> succeeded, how long it took, and what error was recorded.

Keep the limitation clear:

> This is a basic demo Trace Viewer. It is not a full OpenTelemetry replacement
> or a production observability platform.

## 5. Human Review Talk Track

Human Review exists to protect the publishing boundary.

Rules:

- Publishing requires `approved`.
- `pending` cannot publish.
- `rejected` cannot publish.
- Approval happens before Mock Publish.

Suggested explanation:

> Even though this project currently only does Mock Publish, I still built the
> review gate first because Agent workflows need explicit human control before
> any publishing action.

Current limitation:

- Human Review is currently an API/service-level gate.
- It can later become a LangGraph human-in-the-loop node.

## 6. Evaluation Talk Track

Evaluation is currently deterministic and rule-based.

Dimensions:

- `format_score`
- `style_score`
- `consistency_score`
- `compliance_score`
- `completeness_score`
- `overall_score`

The report also includes:

- Issues.
- Suggestions.
- Platform-level score breakdowns.

Important limitation:

> This is not LLM-as-judge. It is also not production-grade content safety
> review. It is a structured baseline so the project can demonstrate evaluation
> loops before connecting real model providers.

## 7. Current Limits

State these clearly during the demo:

- The project does not connect to a real LLM provider.
- The project does not support real platform publishing.
- The project does not include a complex authentication system.
- The project does not promise production deployment readiness.
- Mock Publish is not real publishing.
- The Trace Viewer is demo-level observability.
- Evaluation is rule-based, not LLM-as-judge.

## 8. One-Minute Interview Introduction

> ContentOps Agent is my enterprise-style AI Agent application for
> multi-platform content operations. The point is not just to build a content
> publishing tool. I wanted to abstract the problem into an observable,
> reviewable, and evaluable Agent workflow platform.
>
> A user enters one source article or idea, selects platforms like WeChat,
> Zhihu, Bilibili, Xiaohongshu, and Douyin, and the system generates
> platform-specific previews through a PlatformAdapter architecture. Behind that,
> there is a deterministic LangGraph workflow skeleton with Agent Run and Agent
> Step tracing, so I can show `intake`, `platform_strategy`,
> `preview_generation`, and `finish` as visible workflow steps.
>
> I also added a Human Review gate before Mock Publish, because Agent systems
> should not publish without explicit approval. Finally, I added a rule-based
> Evaluation Report so generated previews can be scored and discussed. The
> current version intentionally does not call real LLMs or real platform APIs;
> it focuses on clean architecture, workflow boundaries, traceability, review,
> evaluation, and PR-based engineering practice.

## Closing Line

> The key engineering idea is: I am not only generating content. I am building
> the control plane around an Agent workflow: adapters, trace, review,
> evaluation, and safe publish boundaries.
