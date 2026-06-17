"""WeChat Official Accounts platform adapter.

WeChat Official Accounts (微信公众号) content style:
- Long-form, formal, paragraph-based.
- Rich text formatting (headings, quotes, images).
- Title limited to 64 characters.
- Cover image is strongly recommended.
- External links restricted in some account tiers.
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

_TITLE_MAX_LENGTH = 64
_BODY_MIN_LENGTH = 100


class WeChatAdapter(PlatformAdapter):
    """Adapter for WeChat Official Accounts content."""

    platform = Platform.WECHAT

    @property
    def platform_name(self) -> str:
        return "WeChat Official Accounts"

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against WeChat Official Accounts rules.

        Rules:
        - Title must not exceed 64 characters.
        - Body must be at least 100 characters.
        - Cover image is recommended but not required.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(content.title) > _TITLE_MAX_LENGTH:
            errors.append(
                f"Title exceeds {_TITLE_MAX_LENGTH} characters (got {len(content.title)})",
            )

        if len(content.body.strip()) < _BODY_MIN_LENGTH:
            errors.append(
                f"Body too short (minimum {_BODY_MIN_LENGTH} characters, "
                f"got {len(content.body.strip())})",
            )

        if not content.cover_image_url:
            warnings.append("Cover image is recommended for WeChat articles")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def transform_content(self, content: PlatformContent) -> PlatformContent:
        """Transform content into WeChat Official Accounts format.

        Transformations:
        - Wraps body in <section> with wechat-specific CSS classes.
        - Converts plain text paragraphs into <p> tags.
        - Adds a formatted author line to the summary.
        """
        paragraphs = [p.strip() for p in content.body.split("\n\n") if p.strip()]
        formatted_paragraphs: list[str] = []
        for para in paragraphs:
            escaped = html.escape(para)
            if para.startswith("# "):
                formatted_paragraphs.append(f"<h2>{html.escape(para[2:])}</h2>")
            elif para.startswith("## "):
                formatted_paragraphs.append(f"<h3>{html.escape(para[3:])}</h3>")
            elif para.startswith("> "):
                formatted_paragraphs.append(
                    f"<blockquote>{html.escape(para[2:])}</blockquote>",
                )
            else:
                formatted_paragraphs.append(f"<p>{escaped}</p>")

        body_html = (
            '<section class="wechat-article">\n' + "\n".join(formatted_paragraphs) + "\n</section>"
        )

        adapted_summary = f"{content.summary or content.title}\n📖 {len(content.body)}字 | 原创"

        return content.model_copy(
            update={
                "body": body_html,
                "summary": adapted_summary,
                "metadata": {
                    **content.metadata,
                    "format": "wechat_rich_text",
                    "character_count": len(content.body),
                },
            }
        )

    def build_preview(self, content: PlatformContent) -> PreviewResult:
        """Build a WeChat-style preview."""
        word_count = len(content.body.replace("<", "").replace(">", ""))
        read_time = max(1, round(word_count / 300))
        rendered = f"""\
<div style="max-width:677px;margin:0 auto;padding:20px;font-family:-apple-system,simsun,sans-serif">
  <h1 style="font-size:22px;font-weight:700;margin-bottom:12px">{html.escape(content.title)}</h1>
  <div style="color:#888;font-size:14px;margin-bottom:20px">{content.summary}</div>
  {content.body}
  <div style="margin-top:24px;padding-top:12px;border-top:1px solid #eee;color:#999;font-size:12px">
    WeChat Official Accounts Preview | {word_count}字 | 阅读约{read_time}分钟
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
        raise NotImplementedError("Real WeChat publish is not implemented yet")

    def mock_publish(self, content: PlatformContent) -> PublishResult:
        """Simulate publishing to WeChat."""
        now = datetime.now(timezone.utc)
        return PublishResult(
            platform=self.platform,
            success=True,
            published_url=f"https://mp.weixin.qq.com/s/mock-{id(content):x}",
            published_at=now,
            metadata={
                "mock": True,
                "platform": "wechat",
                "character_count": len(content.body),
                "simulated_audience": "followers",
            },
        )
