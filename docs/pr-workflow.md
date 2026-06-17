# Pull Request Workflow

## Current Stage (Phase 1-2)

The project uses GitHub Flow with Pull Requests. CI workflows for backend and frontend have been configured and enforce ruff, mypy, and pytest on every PR.

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, deployable branch. Protected — no direct pushes. |
| `feature/*` | New features (e.g., `feature/platform-adapter`). |
| `fix/*` | Bug fixes (e.g., `fix/agent-run-status`). |
| `refactor/*` | Code refactoring (e.g., `refactor/split-publish`). |
| `docs/*` | Documentation updates (e.g., `docs/update-architecture`). |
| `chore/*` | Tooling, dependencies, CI, config (e.g., `chore/add-docker-compose`). |

## PR Workflow

```text
1. Create feature branch from main
        │
        ▼
2. Make changes (small commits)
        │
        ▼
3. Run lint, typecheck, tests locally
        │
        ▼
4. Push branch and open PR
        │
        ▼
5. CI runs automatically
        │
        ▼
6. Review and address feedback
        │
        ▼
7. Squash-merge to main
        │
        ▼
8. Delete feature branch
```

## PR Checklist (from PR Template)

- [ ] Read and followed AGENTS.md.
- [ ] Only modified relevant files.
- [ ] Added or updated tests.
- [ ] Updated documentation.
- [ ] Ran `make lint` and `make typecheck`.
- [ ] Ran `make test` and all tests pass.
- [ ] No secrets committed.
- [ ] PR is small enough for review (< 600 lines).

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(scope): description
fix(scope): description
docs(scope): description
test(scope): description
chore(scope): description
```

## Not in MVP

- Branch protection rules are not yet configured.
- Required PR approvals are not yet enforced.
- Automerging is not configured.
