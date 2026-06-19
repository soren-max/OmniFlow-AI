# v0.1.0-alpha Release Checklist

This checklist is for preparing a `v0.1.0-alpha` tag after the release candidate
PRs have been merged. It is intentionally scoped to the current demo-quality
baseline. It does not claim production readiness.

## Release Scope

The `v0.1.0-alpha` release can include:

- Five-platform content preview.
- PlatformAdapter interface and registry.
- Mock Publish through adapters.
- Deterministic LangGraph workflow skeleton.
- Agent Run and Agent Step trace records.
- Basic Trace Viewer.
- Human Review API gate before Mock Publish.
- Rule-based Evaluation Report.
- FastAPI backend and Next.js frontend.
- CI and PR workflow documentation.

## Known Limitations

- Real LLM integration is not included.
- Real platform publishing is not included.
- Mock Publish is not real publishing.
- Complex authentication, authorization, and RBAC are not included.
- Production deployment is not claimed.
- Rule-based Evaluation is not LLM-as-judge.
- The LangGraph skeleton is deterministic and not a full autonomous Agent.
- The Trace Viewer is basic demo observability, not a production tracing system.
- Frontend tests are still a placeholder.

## Local Demo Checklist

Before tagging `v0.1.0-alpha`, verify the local demo path:

1. Start local dependencies with Docker Compose.
2. Start the FastAPI backend.
3. Start the Next.js frontend.
4. Create a content project.
5. Select all five platforms.
6. Generate previews.
7. Confirm `run_id` is visible after Agent Preview.
8. Open the Trace Viewer and confirm run and step records are visible.
9. Approve the project through Human Review.
10. Run Mock Publish after approval.
11. Run Evaluation Report and confirm scores, issues, and suggestions render.

## Interview Demo Checklist

During an interview demo, cover:

1. Project positioning from the README.
2. Adapter-driven preview architecture.
3. Deterministic LangGraph workflow:
   `intake -> platform_strategy -> preview_generation -> finish`.
4. Agent Run / Step Trace and Trace Viewer.
5. Human Review gate before Mock Publish.
6. Rule-based Evaluation Report.
7. Current limitations and roadmap.

Recommended one-line framing:

> ContentOps Agent is not only a content publishing demo; it is a small Agent
> workflow platform with adapters, traceability, human approval, evaluation, and
> safe mock publishing boundaries.

## Pre-Tag Engineering Checklist

Run these checks from a clean checkout of `main`:

```bash
uv run ruff check apps/api
uv run mypy apps/api
uv run pytest apps/api/tests

cd apps/web
pnpm lint
pnpm typecheck
pnpm test
```

Expected current behavior:

- Backend lint passes.
- Backend typecheck passes.
- Backend tests pass.
- Frontend lint passes.
- Frontend typecheck passes.
- Frontend `pnpm test` passes as the current placeholder script.

## GitHub Checklist

Before creating the tag:

1. Confirm all release-blocking PRs are merged.
2. Confirm `main` is green in CI.
3. Confirm README and docs do not claim real LLM integration.
4. Confirm README and docs do not claim real platform publishing.
5. Confirm no `.env`, API keys, tokens, cookies, or passwords are committed.
6. Confirm no generated directories such as `node_modules`, `.venv`, `.next`,
   `dist`, or `build` are committed.
7. Create an annotated tag only after the checks above pass.

Suggested tag:

```bash
git tag -a v0.1.0-alpha -m "v0.1.0-alpha"
git push origin v0.1.0-alpha
```

Do not create a GitHub Release until the tag and notes have been reviewed.
