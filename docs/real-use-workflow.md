# Real Use Workflow

This workflow describes the current personal-use handoff path. It helps a user
prepare platform-specific content and move it into official publishing tools
manually. It does not automate real publishing.

## Flow

1. Generate platform content.
2. Review the adapted content.
3. Run the rule-based Evaluation Report.
4. Copy the platform-specific title, body, and tags.
5. Open the official platform publish page.
6. Manually paste, review, and submit inside the platform.

## Publish Page Handoff

The web demo provides two actions on each platform preview card:

- `打开发布页`: opens the configured official creator or publishing page.
- `复制后打开`: copies the prepared platform content, then opens the official
  creator or publishing page.

The handoff status is intentionally separate from Mock Publish. Opening a
platform page means the user is ready to continue manually; it does not mark the
project as published.

The UI shows this safety reminder:

```text
将打开平台官方发布页，你仍需要手动粘贴、检查并确认发布。
This opens the official publishing page. You still need to review and submit manually.
```

## Checklist

For each platform, verify:

- Title copied.
- Body copied.
- Tags copied, when available.
- Official publish page opened.
- Human still reviews and confirms submission.

## Explicit Non-Goals

OmniFlow-AI currently does not support:

- Automatic login.
- Automatic submit.
- Cookie-based publishing.
- Token-based publishing.
- Bypassing platform review or platform rules.
- Backend real publishing.
- One-click real publishing.

Mock Publish remains a simulation for demo and testing. Official publish page
handoff is a manual productivity helper for personal use.
