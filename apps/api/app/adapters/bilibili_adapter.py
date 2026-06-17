"""Bilibili platform adapter.

Bilibili (B站) content style:
- Video-centric: script-style content with visual references.
- Opening hook to grab attention.
- Body with main content and timestamps.
- Call-to-action closing (like, subscribe, comment).
- Tags important for search and recommendation algorithm.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone

from .base import PlatformAdapter
from .types import (
    Platform,
    PlatformContent,
    PreviewResult,
    PublishResult,
    ValidationResult,
)

_TITLE_MAX_LENGTH = 80
_BODY_MIN_LENGTH = 50
_MIN_TAGS = 3
_MAX_TAGS = 10


class BilibiliAdapter(PlatformAdapter):
    """Adapter for Bilibili content."""

    platform = Platform.BILIBILI

    @property
    def platform_name(self) -> str:
        return "Bilibili"

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against Bilibili platform rules.

        Rules:
        - Title must not exceed 80 characters (B站标题限制).
        - Body should have at least 50 characters for video description.
        - At least 3 tags recommended for discoverability.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(content.title) > _TITLE_MAX_LENGTH:
            errors.append(
                f"Title exceeds {_TITLE_MAX_LENGTH} characters (got {len(content.title)})",
            )

        if len(content.body.strip()) < _BODY_MIN_LENGTH:
            warnings.append(
                f"Video description is very short ({len(content.body.strip())} chars). "
                f"Consider adding more context for SEO.",
            )

        if len(content.tags) < _MIN_TAGS:
            warnings.append(
                f"At least {_MIN_TAGS} tags recommended for Bilibili discoverability "
                f"(got {len(content.tags)})",
            )
        if len(content.tags) > _MAX_TAGS:
            errors.append(f"Maximum {_MAX_TAGS} tags allowed on Bilibili")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def transform_content(self, content: PlatformContent) -> PlatformContent:
        """Transform content into Bilibili video script format.

        Transformations:
        - Structures content as video script: opening → body → ending.
        - Adds timestamp markers for long content.
        - Formats tags with # prefix for B站 style.
        """
        paragraphs = [p.strip() for p in content.body.split("\n\n") if p.strip()]
        formatted_parts: list[str] = []

        for i, para in enumerate(paragraphs):
            escaped = html.escape(para)
            if para.startswith("# "):
                formatted_parts.append(
                    f"<h2>{html.escape(para[2:])}</h2>",
                )
            elif i == 0:
                # Opening hook
                formatted_parts.append(
                    f'<div class="bilibili-opening">{escaped}</div>',
                )
            elif i == len(paragraphs) - 1:
                # Call to action
                formatted_parts.append(
                    f'<div class="bilibili-cta">{escaped}</div>',
                )
            else:
                formatted_parts.append(f"<p>{escaped}</p>")

        body_html = '<div class="bilibili-script">\n' + "\n".join(formatted_parts) + "\n</div>"

        # Format tags with Bilibili # prefix
        bilibili_tags = [f"#{t}" for t in content.tags]

        adapted_title = content.title
        if not adapted_title.endswith(("！", "!", "？", "?")):  # noqa: RUF001
            # Bilibili titles often have engaging suffixes
            pass  # Keep original

        return content.model_copy(
            update={
                "title": adapted_title,
                "body": body_html,
                "tags": bilibili_tags,
                "summary": (content.summary or f"📺 {content.title} | 点赞·投币·收藏"),
                "metadata": {
                    **content.metadata,
                    "format": "bilibili_video_script",
                    "paragraph_count": len(paragraphs),
                    "has_opening": True,
                    "has_cta": True,
                },
            }
        )

    def build_preview(self, content: PlatformContent) -> PreviewResult:
        """Build a Bilibili-style preview."""
        word_count = len(content.body.replace("<", "").replace(">", ""))
        read_time = max(1, round(word_count / 250))
        tags_html = " ".join(
            f'<span style="color:#fb7299;font-size:13px;margin-right:8px">{html.escape(t)}</span>'
            for t in content.tags
        )
        rendered = f"""\
<div style="max-width:700px;margin:0 auto;font-family:-apple-system,'PingFang SC',sans-serif">
  <div style="background:#fb7299;color:white;padding:12px 20px;border-radius:4px 4px 0 0;font-size:13px">
    📺 Bilibili Video Description Preview
  </div>
  <div style="padding:20px;background:#fff;border:1px solid #e5e5e5;border-top:none">
    <h1 style="font-size:20px;font-weight:700;margin-bottom:12px;color:#18191c">{html.escape(content.title)}</h1>
    <div style="color:#9499a0;font-size:13px;margin-bottom:16px">
      {word_count}字 | 📅 模拟发布于今天
    </div>
    {tags_html}
    <hr style="margin:16px 0;border:none;border-top:1px solid #f1f2f3" />
    {content.body}
    <div style="margin-top:20px;padding:12px;background:#f6f7f8;border-radius:4px;color:#9499a0;font-size:12px;text-align:center">
      👍 点赞 · 💬 评论 · 🔄 转发 · ⭐ 收藏
    </div>
  </div>
</div>"""
        return PreviewResult(
            platform=self.platform,
            rendered_html=rendered,
            word_count=word_count,
            estimated_read_time_min=read_time,
        )

    def publish(self, content: PlatformContent) -> PublishResult:
        """Real publish — not implemented in mock stage."""
        raise NotImplementedError("Real Bilibili publish is not implemented yet")

    def mock_publish(self, content: PlatformContent) -> PublishResult:
        """Simulate publishing to Bilibili."""
        now = datetime.now(timezone.utc)
        return PublishResult(
            platform=self.platform,
            success=True,
            published_url=f"https://www.bilibili.com/video/mock-{id(content):x}",
            published_at=now,
            metadata={
                "mock": True,
                "platform": "bilibili",
                "video_id": f"mock-{id(content):x}",
                "word_count": len(content.body),
            },
        )
