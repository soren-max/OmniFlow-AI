# AGENTS.md

## Project Name

ContentOps Agent

## Project Goal

Build an enterprise-style AI Agent application for multi-platform content operations.

The system helps users input a source article or content idea, then uses an Agent workflow to:

1. Understand the content intent.
2. Adapt the content for different platforms.
3. Generate platform-specific titles, hooks, tags, and formats.
4. Run compliance and quality checks.
5. Build previews.
6. Require human approval before publishing.
7. Execute mock publishing or real publishing through platform adapters.
8. Record Agent traces, tool calls, evaluation results, and user feedback.

This repository should demonstrate production-quality engineering practices for AI Agent application development.

## Target Role Alignment

This project is designed to support preparation for AI Agent application development and AI coding agent internships.

The implementation should emphasize:

* Agent workflow orchestration.
* Tool calling.
* Multi-agent collaboration.
* Human-in-the-loop review.
* Code quality.
* Testing.
* Observability.
* Evaluation.
* Modular architecture.
* Pull Request based development.

## Tech Stack

Backend:

* Python 3.12
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* LangGraph
* PostgreSQL
* Redis
* pytest
* ruff
* mypy
* uv

Frontend:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* pnpm

Infrastructure:

* Docker Compose
* GitHub Actions
* OpenTelemetry or structured logging

Optional:

* Qdrant for vector search
* Playwright for browser automation
* Celery or Dramatiq for async jobs

## Repository Structure

Expected structure:

```text
contentops-agent/
├── AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   ├── shared/
│   └── prompts/
├── docs/
├── evals/
├── scripts/
└── .github/
```

Do not create random top-level directories unless necessary.

## Core Modules

Backend modules should be organized as:

```text
apps/api/app/
├── main.py
├── core/
├── api/
├── models/
├── schemas/
├── services/
├── repositories/
├── agents/
├── adapters/
├── evaluators/
└── telemetry/
```

Module responsibilities:

* `core/`: configuration, security, logging, database setup.
* `api/`: FastAPI route definitions.
* `models/`: SQLAlchemy database models.
* `schemas/`: Pydantic request and response models.
* `repositories/`: database access layer.
* `services/`: business logic.
* `agents/`: LangGraph workflows and Agent nodes.
* `adapters/`: platform-specific publishing adapters.
* `evaluators/`: quality evaluation logic.
* `telemetry/`: trace logging, metrics, and run records.

## Development Rules

Always follow these rules:

1. Read this `AGENTS.md` before making changes.
2. Understand the current repository structure before editing files.
3. Make the smallest correct change.
4. Do not rewrite unrelated files.
5. Do not introduce unnecessary dependencies.
6. Do not hardcode API keys, tokens, cookies, passwords, or secrets.
7. Use environment variables for configuration.
8. Update `.env.example` when adding new environment variables.
9. Add or update tests when changing behavior.
10. Update documentation when changing architecture, setup, or public APIs.
11. Keep code readable, typed, and modular.
12. Prefer explicit names over clever abstractions.
13. Do not bypass linting, type checking, or tests.
14. Do not directly push to `main`.
15. Every meaningful change should go through a feature branch and Pull Request.

## Git Workflow

Use GitHub Flow.

Branches:

* `main`: stable and deployable.
* `feature/*`: new features.
* `fix/*`: bug fixes.
* `refactor/*`: refactoring.
* `docs/*`: documentation.
* `chore/*`: tooling, dependencies, CI, configuration.

Examples:

```bash
git checkout -b feature/platform-adapter
git checkout -b fix/agent-run-status
git checkout -b docs/update-architecture
```

## Commit Message Convention

Use Conventional Commits.

Allowed types:

* `feat`
* `fix`
* `docs`
* `style`
* `refactor`
* `test`
* `chore`
* `perf`
* `ci`
* `build`

Examples:

```text
feat(agent): add content rewrite workflow
fix(adapter): handle empty platform content
docs(readme): add local development guide
test(api): add project creation tests
ci(github): add backend test workflow
refactor(service): split publish service
```

Do not use vague commit messages such as:

```text
update
fix bug
changes
final
```

## Pull Request Rules

Each PR must be small and focused.

A good PR:

* Solves one problem.
* Has a clear title.
* Includes tests when behavior changes.
* Passes CI.
* Updates docs if needed.
* Does not include unrelated formatting changes.
* Starts from the latest `main` unless there is an explicit reason not to.
* Does not push directly to `main`.
* Does not delete, skip, or weaken tests to bypass CI.
* Reports changed files, tests run, and known limitations when complete.
* Keeps documentation accurate and avoids claiming planned work as completed.

Preferred PR size:

* Small: under 300 changed lines.
* Acceptable: under 600 changed lines.
* Large PRs should be split.

PR title examples:

```text
feat(adapter): add base platform adapter
feat(agent): add content adaptation workflow
fix(api): validate project target platforms
docs(agent): document workflow nodes
test(evaluator): add consistency score tests
```

## Pull Request Checklist

Before opening or updating a PR, verify:

```bash
make format
make lint
make typecheck
make test
```

If the repository does not yet have these commands, add them before relying on them.

## Definition of Done

A task is done only when:

* The feature works for the intended use case.
* Tests are added or updated.
* Lint passes.
* Type checks pass.
* No secrets are committed.
* Documentation is updated if needed.
* The change is small enough for review.
* The implementation follows existing architecture.
* The code is understandable to a future maintainer.

## Coding Standards

Python:

* Use Python 3.12.
* Use type hints for public functions.
* Use Pydantic models for API input and output.
* Keep FastAPI routes thin.
* Put business logic in services.
* Put database logic in repositories.
* Use SQLAlchemy models only for persistence.
* Avoid mixing API, database, and Agent logic in one file.
* Use async only when it provides real value.
* Do not swallow exceptions silently.
* Log meaningful errors with context.

TypeScript:

* Use TypeScript strictly.
* Prefer server components where appropriate.
* Keep UI components small and reusable.
* Put API client logic in `lib/`.
* Put shared types in `types/`.
* Avoid large components over 300 lines.
* Do not duplicate backend schema names manually if generated types exist.

Agent:

* Agent nodes should be deterministic where possible.
* Each Agent node should have a clear input and output schema.
* Do not let one Agent node do everything.
* Prefer small nodes:

  * content intake
  * platform strategy
  * content rewrite
  * title and hook generation
  * compliance review
  * format adaptation
  * preview generation
  * human approval
  * publish execution
  * evaluation
* Record every Agent run.
* Record every Agent step.
* Record tool calls.
* Record latency.
* Record errors.
* Record token usage if available.
* Human approval is required before publishing.

## Platform Adapter Rules

All platforms must implement the same adapter interface.

The base adapter should expose:

```python
class PlatformAdapter:
    platform_name: str

    def validate_content(self, content):
        raise NotImplementedError

    def transform_content(self, content):
        raise NotImplementedError

    def build_preview(self, content):
        raise NotImplementedError

    def publish(self, content):
        raise NotImplementedError

    def mock_publish(self, content):
        raise NotImplementedError
```

Do not hardcode platform-specific logic inside Agent nodes.

## Testing Rules

* Every backend route must have a corresponding test.
* Tests must be in `apps/api/tests/`.
* Use pytest for backend tests.
* Use httpx AsyncClient for API tests.
* Do not delete or skip tests to make CI pass.
* Test failure is a bug — fix the code, not the test.

## Current Stage: Demo-quality Agent Workflow Platform / Release Candidate Preparation

This repository is no longer in the bootstrap-only stage. The current baseline is
a demo-quality Agent workflow platform preparing for a release candidate.

Current completed baseline:

* Five-platform preview for WeChat, Zhihu, Bilibili, Xiaohongshu, and Douyin.
* PlatformAdapter interface and registry.
* Mock Publish through platform adapters.
* Deterministic LangGraph workflow skeleton.
* Agent Run and Agent Step trace records.
* Human Review API gate before Mock Publish.
* Rule-based Evaluation reports.
* Basic Trace Viewer when present in the current branch.
* FastAPI backend, Next.js frontend, and CI / PR workflow.

## Allowed Current Scope

The following work is allowed when it is small, reviewed, tested, and aligned
with the existing architecture:

* PlatformAdapter improvements and new mock adapter behavior.
* Mock Publish improvements.
* Deterministic LangGraph workflow skeleton improvements.
* Agent Run / Step Trace improvements.
* Human Review API gate improvements.
* Rule-based Evaluation improvements.
* Basic Trace Viewer and demo-readiness improvements.
* Documentation and interview demo materials.
* Test coverage, linting, type checking, and CI quality improvements.
* Small refactors that preserve behavior and clarify module boundaries.

## Still Out of Scope

The following remain out of scope unless explicitly requested and scoped in a
separate focused PR:

* Real platform publishing.
* Browser automation with real user accounts.
* Cookies, tokens, account passwords, or session automation.
* Real LLM provider integration.
* Hardcoded API keys, tokens, cookies, passwords, or secrets.
* Complex authentication, authorization, or RBAC.
* Production deployment claims or production-readiness claims.
* Large all-in-one PRs that are difficult to review.
* Bypassing tests, linting, type checking, or CI gates.
* Committing `.env` files or other local secret files.
* Messy top-level directories unrelated to the monorepo structure.

## Documentation Accuracy

Documentation must distinguish completed functionality from planned work.

Use precise language:

* Mock Publish is not real publishing.
* Rule-based Evaluation is not LLM-as-judge.
* The deterministic LangGraph skeleton is not a complete autonomous Agent.
* Demo-quality does not mean production-ready SaaS.
* Trace Viewer, when present, is basic demo observability, not a full observability
  platform.
* Real LLM integration and real platform publishing must be described as future
  work unless an explicit scoped PR implements them.
