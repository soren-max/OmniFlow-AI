# Real-Use Workflow

This document describes the personal-use publishing workflow for OmniFlow-AI.

**Important:** OmniFlow-AI is designed for assisted manual publishing. It does not
automatically submit content to real platforms, does not store cookies or account
passwords, and does not use browser automation (Playwright / Selenium) to bypass
official workflows.

---

## Personal-Use Publishing Workflow

```
Generate → Review → Evaluate → Export → Copy → Open official publish page → Manual submit
```

### Step-by-step

1. **Generate** — Select target platforms and generate platform-specific content
   through the PlatformAdapter pipeline.

2. **Review** — Inspect the rendered preview, validation warnings, and metadata
   for each platform. The Trace Viewer shows the full adaptation steps.

3. **Evaluate** — Run rule-based evaluation to check consistency, compliance,
   and readability scores.

4. **Export** — Export a publish package as Markdown or JSON. Draft and rejected
   project exports include status/warning metadata for inspection before manual
   publishing.

5. **Copy** — Copy platform-specific title, body, and tags using the copy buttons
   on each PreviewCard. The "复制内容" button copies the full platform text;
   "复制标题" and "复制标签" copy individual fields.

6. **Open official publish page** — Use the "打开发布页" or "复制后打开" button
   to open the target platform's official publishing interface. The "复制后打开"
   button copies content first, then opens the page.

7. **Manual submit** — Paste the copied content into the platform's official
   publishing form, review, and submit manually. OmniFlow-AI does not perform
   automatic submission.

---

## What This Workflow Supports

| Feature | Description |
|---------|-------------|
| Multi-platform generation | WeChat, Zhihu, Bilibili, Xiaohongshu, Douyin |
| Content review | Rendered previews, validation warnings, trace viewer |
| Rule-based evaluation | Consistency, compliance, readability scores |
| Publish package export | Markdown / JSON export with metadata |
| Copy actions | Per-field copy (title, body, tags) and full content copy |
| Publish handoff | Open official publish page; optional copy-before-open |
| Manual publish checklist | Track copy and handoff status per platform |

---

## What This Workflow Does NOT Do

- ❌ Does not automatically submit content to real platforms.
- ❌ Does not store cookies, account passwords, or session tokens.
- ❌ Does not use Playwright, Selenium, or any browser automation.
- ❌ Does not bypass platform official publishing workflows.
- ❌ Does not mark content as "published" on real platforms.
- ❌ Does not claim to support real automatic publishing.

The platform official publish page is opened in a new browser tab using
`window.open` with `noopener,noreferrer` for security. No credentials, tokens,
or API calls are sent — the page is presented for the user to complete manually.

---

## Related Documentation

- [API Design](./api-design.md) — API reference for export and handoff endpoints.
- [README](../README.md) — Project overview and quick start.
- [Architecture](./architecture.md) — PlatformAdapter and system design.
