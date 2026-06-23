# Real-Use Workflow

This document describes the personal-use publishing workflow for OmniFlow-AI.

**Important:** OmniFlow-AI is designed for assisted manual publishing. It does not
automatically submit content to real platforms, does not store cookies or account
passwords, and does not use browser automation (Playwright / Selenium) to bypass
official workflows.

---

## Personal-Use Publishing Workflow

```
DeepSeek Generate → Preview → Human Review → Evaluation → Save Draft → Edit Draft → Export / Copy → Open Official Publish Page → Manual Submit
```

### Step-by-step

1. **Generate** — Select target platforms and generate platform-specific content
   through the PlatformAdapter pipeline.

2. **Preview** — Inspect the rendered preview, validation warnings, and metadata
   for each platform. The Trace Viewer shows the full adaptation steps.

3. **Human Review** — Approve or reject the generated project inside
   OmniFlow-AI before running Mock Publish. This is a system review gate, not
   approval from any external platform.

4. **Evaluate** — Run rule-based evaluation to check consistency, compliance,
   and readability scores.

5. **Save Draft** — Save a platform preview into the OmniFlow-AI system draft
   workspace. This is not the platform official draft box and does not write
   content into Xiaohongshu, Douyin, Zhihu, WeChat, or Bilibili backends.

6. **Edit Draft** — Edit the system draft title, body, tags, and notes before
   manual publishing.

7. **Export / Copy** — Export a publish package or a single draft as Markdown
   or JSON. Draft and rejected
   project exports include status/warning metadata for inspection before manual
   publishing. You can also copy platform-specific title, body, and tags using
   the copy buttons on each PreviewCard or from the draft workspace.

8. **Open Official Publish Page** — Use the "打开发布页" or "复制后打开" button
   to open the target platform's official publishing interface. The "复制后打开"
   button copies content first, then opens the page.

9. **Manual Submit** — Paste the copied content into the platform's official
   publishing form, review, and submit manually. OmniFlow-AI does not perform
   automatic submission.

---

## What This Workflow Supports

| Feature | Description |
|---------|-------------|
| Multi-platform generation | WeChat, Zhihu, Bilibili, Xiaohongshu, Douyin |
| Content review | Rendered previews, validation warnings, trace viewer |
| Rule-based evaluation | Consistency, compliance, readability scores |
| System publish drafts | Save, list, edit, copy, export, and hand off OmniFlow-AI internal drafts |
| Publish package export | Markdown / JSON export with metadata |
| Copy actions | Per-field copy (title, body, tags) and full content copy |
| Publish handoff | Open official publish page; optional copy-before-open |
| Manual publish checklist | Track copy and handoff status per platform |

---

## What This Workflow Does NOT Do

- ❌ Does not automatically submit content to real platforms.
- ❌ Does not save content into platform official draft boxes.
- ❌ Does not store cookies, account passwords, or session tokens.
- ❌ Does not use Playwright, Selenium, or any browser automation.
- ❌ Does not bypass platform official publishing workflows.
- ❌ Does not mark content as "published" on real platforms.
- ❌ Does not claim to support real automatic publishing.

The platform official publish page is opened in a new browser tab using
`window.open` with `noopener,noreferrer` for security. No credentials, tokens,
or API calls are sent — the page is presented for the user to complete manually.

The publish draft workspace is only an OmniFlow-AI system feature. Its
`draft`, `reviewed`, `exported`, `handoff_opened`, and `archived` statuses record
the local manual workflow state; they are not official platform draft or publish
states.

---

## Related Documentation

- [API Design](./api-design.md) — API reference for export and handoff endpoints.
- [README](../README.md) — Project overview and quick start.
- [Architecture](./architecture.md) — PlatformAdapter and system design.
