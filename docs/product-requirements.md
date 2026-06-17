# Product Requirements Document

## Current Stage (MVP Bootstrap)

This document captures the current bootstrap-stage product direction. The repository has the engineering skeleton, basic project APIs, mock platform adapters, a multi-platform preview UI, and a mock publish loop. Agent orchestration, real publishing, persistence, evaluation, and human approval remain future work.

## Product Vision

ContentOps Agent is an AI-powered platform that helps content creators and enterprise operations teams:

1. Input source content or content ideas.
2. Automatically adapt content for multiple platforms.
3. Generate platform-specific titles, hooks, and tags.
4. Run compliance and quality checks.
5. Preview content across platforms.
6. Require human approval before publishing.
7. Execute mock or real publishing.
8. Record and evaluate every Agent run.

## Target Platforms (Future)

- **WeChat Official Accounts** — long-form articles with rich media.
- **Zhihu** — Q&A style, knowledge-sharing format.
- **Bilibili** — video descriptions, bullet comments, community style.
- **Xiaohongshu (RED)** — image-first, short-form, trending style.
- **Douyin** — short-video scripts, three-second hooks, shot lists, and engagement prompts.

## User Personas (Future)

- **Content Creator**: writes source content, reviews adaptations, publishes.
- **Operations Manager**: defines platform strategies, sets compliance rules.
- **Reviewer**: approves content before publishing.

## Current MVP Scope

- Create content projects.
- Generate previews for five platforms.
- Select platforms and execute mock publish.
- Return per-platform mock publish URLs and messages.

Real publishing is not supported in the current MVP. Future real publishing must
extend PlatformAdapter, require Human Review, require explicit authorization, and
use secure credential management.

## Future Scope (Not Yet Implemented)

The following are **out of scope** for the bootstrap stage and will be addressed in future sprints:

- Content understanding / intent analysis.
- Platform style adaptation.
- Title / hook / tag generation.
- Compliance checks.
- Full preview generation beyond deterministic mock adapters.
- Human approval workflow.
- Real publishing.
- Agent run tracing.
- Evaluation metrics.
- User authentication and authorization.
