"""Xiaohongshu (RED) platform adapter.

Xiaohongshu (小红书) content style:
- Short-form, image-first, conversational.
- Emoji-friendly to express tone and emotion.
- Brief, scannable paragraphs.
- Cover image is essential.
- Heavy use of tags/mentions for discoverability.
- Title with engaging hooks and emojis.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone

from .base import PlatformAdapter
from .types import (
    Platform,
    PlatformContent,
    PreviewResult,
    PublishResult,
    ValidationResult,
)

_TITLE_MAX_LENGTH = 40
_BODY_MAX_LENGTH = 1000
_MIN_TAGS = 3
_MAX_TAGS = 15


class XiaohongshuAdapter(PlatformAdapter):
    """Adapter for Xiaohongshu (RED) content."""

    platform = Platform.XIAOHONGSHU

    @property
    def platform_name(self) -> str:
        return "Xiaohongshu (RED)"

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against Xiaohongshu platform rules.

        Rules:
        - Title should be under 40 characters (shorter is better).
        - Body should be under 1000 characters (scannable format).
        - At least 3 tags recommended; maximum 15 tags.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(content.title) > _TITLE_MAX_LENGTH:
            warnings.append(
                f"Title exceeds recommended {_TITLE_MAX_LENGTH} characters "
                f"(got {len(content.title)}). Xiaohongshu titles work best when short.",
            )

        body_len = len(content.body)
        if body_len > _BODY_MAX_LENGTH:
            errors.append(
                f"Body exceeds {_BODY_MAX_LENGTH} characters "
                f"(got {body_len}). Xiaohongshu favors concise content.",
            )

        if len(content.tags) < _MIN_TAGS:
            warnings.append(
                f"At least {_MIN_TAGS} tags recommended for Xiaohongshu "
                f"discoverability (got {len(content.tags)})",
            )
        if len(content.tags) > _MAX_TAGS:
            errors.append(f"Maximum {_MAX_TAGS} tags allowed on Xiaohongshu")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def transform_content(self, content: PlatformContent) -> PlatformContent:
        """Transform content into Xiaohongshu style.

        Transformations:
        - Splits long paragraphs into shorter, scannable lines.
        - Adds emoji decorations to title and hooks.
        - Converts tags to Xiaohongshu #tag format.
        - Wraps body in lightweight HTML structure.
        """
        # Split body into short paragraphs (2-3 sentences max each)
        paragraphs = [p.strip() for p in content.body.split("\n\n") if p.strip()]
        short_paragraphs: list[str] = []
        for para in paragraphs:
            # Further split long paragraphs by sentences
            if len(para) > 100:
                sentences = re.split(r"(?<=[。！？.!?])", para)  # noqa: RUF001
                current = ""
                for sent in sentences:
                    if sent.strip() and len(current + sent) > 80:
                        if current.strip():
                            short_paragraphs.append(current.strip())
                        current = sent
                    else:
                        current += sent
                if current.strip():
                    short_paragraphs.append(current.strip())
            else:
                short_paragraphs.append(para)

        formatted_paragraphs: list[str] = []
        for para in short_paragraphs:
            escaped = html.escape(para)
            if para.startswith("# "):
                formatted_paragraphs.append(
                    f"<h2>{html.escape(para[2:])} ✨</h2>",
                )
            else:
                formatted_paragraphs.append(
                    f'<p style="margin-bottom:12px;line-height:1.8">{escaped}</p>',
                )

        body_html = '<div class="xhs-post">\n' + "\n".join(formatted_paragraphs) + "\n</div>"

        # Format tags with # prefix
        xhs_tags = [f"#{t.replace(' ', '')}" for t in content.tags]

        # Decorate title with emojis if none present
        adapted_title = content.title
        if not re.search(r"[\U0001F300-\U0001FFFF]", adapted_title):
            adapted_title = f"✨ {adapted_title}"

        # Add emoji-decorated hooks
        adapted_hooks = [f"🔥 {h}" if not h.startswith("🔥") else h for h in content.hooks]

        return content.model_copy(
            update={
                "title": adapted_title,
                "body": body_html,
                "hooks": adapted_hooks,
                "tags": xhs_tags,
                "summary": (
                    content.summary or f"📝 {content.title} ｜ 干货分享"  # noqa: RUF001
                ),
                "metadata": {
                    **content.metadata,
                    "format": "xiaohongshu_post",
                    "paragraph_count": len(short_paragraphs),
                    "emoji_style": True,
                },
            }
        )

    def build_preview(self, content: PlatformContent) -> PreviewResult:
        """Build a Xiaohongshu-style preview."""
        word_count = len(content.body.replace("<", "").replace(">", ""))
        read_time = max(1, round(word_count / 200))
        tags_html = "\n".join(
            f'<span style="color:#ff2442;font-size:12px;margin-right:8px">{html.escape(t)}</span>'
            for t in content.tags
        )
        # Simulate a mobile card layout
        rendered = f"""\
<div style="max-width:400px;margin:0 auto;font-family:-apple-system,'PingFang SC',sans-serif;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
  <div style="height:200px;background:linear-gradient(135deg,#ff6b6b,#ffd93d);display:flex;align-items:center;justify-content:center;color:white;font-size:36px">
    📸
  </div>
  <div style="padding:16px">
    <h1 style="font-size:16px;font-weight:700;margin-bottom:8px;color:#222">{html.escape(content.title)}</h1>
    <div style="color:#666;font-size:13px;margin-bottom:12px;line-height:1.6">
      {content.body[:200]}{"..." if len(content.body) > 200 else ""}
    </div>
    <div style="margin-bottom:12px">
      {tags_html}
    </div>
    <div style="display:flex;justify-content:space-between;color:#999;font-size:12px;padding-top:12px;border-top:1px solid #f0f0f0">
      <span>❤️ {word_count}字</span>
      <span>💬 模拟发布于今天</span>
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
        raise NotImplementedError("Real Xiaohongshu publish is not implemented yet")

    def mock_publish(self, content: PlatformContent) -> PublishResult:
        """Simulate publishing to Xiaohongshu."""
        now = datetime.now(timezone.utc)
        return PublishResult(
            platform=self.platform,
            success=True,
            published_url=f"https://www.xiaohongshu.com/discovery/item/mock-{id(content):x}",
            published_at=now,
            metadata={
                "mock": True,
                "platform": "xiaohongshu",
                "note_id": f"mock-{id(content):x}",
                "word_count": len(content.body),
            },
        )
