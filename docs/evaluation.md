# Evaluation

## Current Stage

No evaluation system has been implemented. The `evals/` directory at the project root is prepared for:

- `evals/datasets/` — test datasets for evaluating Agent performance.
- `evals/reports/` — generated evaluation reports.

The deterministic LangGraph preview workflow now records in-memory Agent Run and
Agent Step traces. Those records include status, input/output snapshots, latency,
and errors, which gives future Evaluation work a baseline event history. Current
trace records are not evaluation scores and are not persisted to PostgreSQL yet.

## Intended Evaluation Framework (Future)

### Dimensions

| Dimension | Description | Metric |
|-----------|-------------|--------|
| Consistency | Content matches original intent | 0.0 - 1.0 |
| Compliance | Content follows platform rules | Pass / Fail |
| Readability | Content is easy to read and understand | 0.0 - 1.0 |
| Title Quality | Titles are engaging and accurate | 0.0 - 1.0 |
| Hook Quality | Opening hooks capture attention | 0.0 - 1.0 |
| Tag Relevance | Tags are relevant and discoverable | 0.0 - 1.0 |

### Evaluation Process (Future)

1. User submits source content.
2. Agent generates adapted content for each platform.
3. Each adapted piece is evaluated against the dimensions above.
4. An overall quality score is computed.
5. The evaluation result is stored alongside the Agent run.
6. Human reviewer can see the scores before approving.

### Data Collection (Future)

- Every Agent run is recorded with step traces in the current in-memory trace
  service.
- Tool calls, latency, errors, and token usage will be logged as the workflow
  expands. The current deterministic workflow records latency and errors, while
  token usage is absent because no LLM is called.
- User feedback (ratings and comments) is collected.
- Evaluation datasets can be used for regression testing.

## Not in MVP

The evaluation framework, metrics, persistent evaluation data collection, and
token usage reporting are not yet implemented. The current trace service only
captures deterministic workflow run/step records for future evaluation inputs.
