# Real Use Workflow

This document describes the personal-use workflow for turning generated previews
into a manual publishing package.

## Flow

```text
Generate -> Review -> Evaluate -> Export -> Copy -> Manual publish
```

1. Generate five-platform previews from one source title and body.
2. Review the generated content in the dashboard.
3. Approve or reject through Human Review.
4. Run the rule-based Evaluation Report when quality feedback is useful.
5. Export the publish package as Markdown or JSON.
6. Copy platform-specific title, tags, or full content from the Preview Cards.
7. Manually paste the content into the official platform publishing UI.

## Export Status

Export is allowed for any review state:

- `pending` exports are marked as draft.
- `approved` exports are ready for manual publishing.
- `rejected` exports include a warning so the user can inspect before posting.

## What The Package Contains

Each export includes:

- `project_id`
- `title`
- `created_at`
- selected platform identifiers
- per-platform title, body, hashtags, summary, CTA, notes, and copy text
- review status
- evaluation summary when available
- export timestamp

If Evaluation has not been generated yet, the package explicitly says:

```text
Evaluation not generated yet.
```

## Boundaries

This workflow is not automatic publishing.

- It does not use browser automation.
- It does not use Cookies, Tokens, or account passwords.
- It does not bypass platform official publishing flows.
- It does not call real platform publishing APIs.

The export feature is for organizing generated content so a person can review it
and publish manually.
