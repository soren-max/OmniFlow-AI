# Evaluation

## Current Stage

The project now includes a deterministic, rule-based content quality evaluation
report for generated platform previews. It is not LLM-as-judge, does not call a
model provider, and does not use hidden prompts.

Current endpoints:

- `POST /api/projects/{project_id}/evaluation`
- `GET /api/projects/{project_id}/evaluation`

The evaluator reads persisted preview records, computes platform-level scores,
stores the report in PostgreSQL, and returns the latest report through the API.

## Current Dimensions

Each platform preview receives scores from 0 to 100:

| Dimension | Current rule-based signal |
|-----------|---------------------------|
| `format_score` | Required title, content length, rendered preview HTML |
| `style_score` | Platform-specific metadata such as scripts, hashtags, shots, or summaries |
| `consistency_score` | Source title and source-text overlap with adapted content |
| `compliance_score` | Adapter validation errors and warnings |
| `completeness_score` | Summary, hooks, and word-count completeness |
| `overall_score` | Average of the five dimension scores |

Reports also include:

- `average_score`
- platform scores for all evaluated previews
- `issues`
- `suggestions`

## Supported Platforms

The current evaluator supports previews for all five adapters:

- WeChat Official Accounts / `wechat`
- Zhihu / `zhihu`
- Bilibili / `bilibili`
- Xiaohongshu / `xiaohongshu`
- Douyin / `douyin`

## Limits

This is intentionally a baseline evaluator. It is useful for deterministic checks
and regression tests, but it is not a semantic quality judge. Future PRs can add
LLM-as-judge, reviewer feedback, dataset-based regression reports, or evaluation
inside the LangGraph workflow after explicit approval.
