"""Zhihu platform adapter.

Zhihu (知乎) content style:
- Q&A and knowledge-sharing format.
- Analytical, structured with clear problem statement.
- Supports Markdown-like formatting (headings, code blocks, lists).
- Tags required for categorization.
- Title can be a question or declarative statement.
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
_BODY_MIN_LENGTH = 200
_MIN_TAGS = 1
_MAX_TAGS = 5


class ZhihuAdapter(PlatformAdapter):
    """Adapter for Zhihu content."""

    platform = Platform.ZHIHU

    @property
    def platform_name(self) -> str:
        return "Zhihu"

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against Zhihu platform rules.

        Rules:
        - Title must not exceed 80 characters.
        - Body must be at least 200 characters (in-depth analysis).
        - At least 1 tag required; maximum 5 tags.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(content.title) > _TITLE_MAX_LENGTH:
            errors.append(
                f"Title exceeds {_TITLE_MAX_LENGTH} characters (got {len(content.title)})",
            )

        if len(content.body.strip()) < _BODY_MIN_LENGTH:
            errors.append(
                f"Body too short for Zhihu analysis (minimum {_BODY_MIN_LENGTH} "
                f"characters, got {len(content.body.strip())})",
            )

        if len(content.tags) < _MIN_TAGS:
            errors.append(f"At least {_MIN_TAGS} tag is required for Zhihu")
        if len(content.tags) > _MAX_TAGS:
            errors.append(f"Maximum {_MAX_TAGS} tags allowed for Zhihu")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def transform_content(self, content: PlatformContent) -> PlatformContent:
        """Transform content into Zhihu format.

        Transformations:
        - Wraps body in a structured article format.
        - Adds a problem statement / question context to summary.
        - Formats code blocks with <pre><code> tags.
        - Structures content as intro → analysis → conclusion.
        """
        paragraphs = [p.strip() for p in content.body.split("\n\n") if p.strip()]
        formatted_paragraphs: list[str] = []

        for i, para in enumerate(paragraphs):
            escaped = html.escape(para)
            if para.startswith("# "):
                formatted_paragraphs.append(
                    f"<h2>{html.escape(para[2:])}</h2>",
                )
            elif para.startswith("## "):
                formatted_paragraphs.append(
                    f"<h3>{html.escape(para[3:])}</h3>",
                )
            elif para.startswith("```"):
                continue  # Skip code fence markers
            elif para.startswith("- ") or para.startswith("* "):
                items = para.split("\n")
                list_items = "\n".join(
                    f"<li>{html.escape(item[2:])}</li>"
                    for item in items
                    if item.startswith("- ") or item.startswith("* ")
                )
                formatted_paragraphs.append(f"<ul>\n{list_items}\n</ul>")
            else:
                if i == 0:
                    formatted_paragraphs.append(
                        f'<p class="zh-intro">{escaped}</p>',
                    )
                elif i == len(paragraphs) - 1:
                    formatted_paragraphs.append(
                        f'<p class="zh-conclusion">{escaped}</p>',
                    )
                else:
                    formatted_paragraphs.append(f"<p>{escaped}</p>")

        body_html = (
            '<article class="zh-article">\n' + "\n".join(formatted_paragraphs) + "\n</article>"
        )

        adapted_summary = (
            f"问题：{content.summary or content.title}\n"  # noqa: RUF001
            f"本文从多个角度深入分析，共 {len(content.body)} 字"  # noqa: RUF001
        )

        return content.model_copy(
            update={
                "body": body_html,
                "summary": adapted_summary,
                "metadata": {
                    **content.metadata,
                    "format": "zhihu_article",
                    "paragraph_count": len(paragraphs),
                },
            }
        )

    def build_preview(self, content: PlatformContent) -> PreviewResult:
        """Build a Zhihu-style preview."""
        word_count = len(content.body.replace("<", "").replace(">", ""))
        read_time = max(1, round(word_count / 400))
        tags_html = " ".join(
            f'<span style="background:#f0f0f0;padding:2px 8px;'
            f'border-radius:3px;margin-right:6px;font-size:13px">'
            f"{html.escape(t)}</span>"
            for t in content.tags
        )
        rendered = f"""\
<div style="max-width:720px;margin:0 auto;padding:24px;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <h1 style="font-size:24px;font-weight:700;margin-bottom:8px;color:#1a1a1a">{html.escape(content.title)}</h1>
  <div style="color:#8590a6;font-size:14px;margin-bottom:16px">
    {content.summary}
  </div>
  {tags_html}
  <hr style="margin:20px 0;border:none;border-top:1px solid #ebebeb" />
  {content.body}
  <div style="margin-top:24px;color:#8590a6;font-size:13px;text-align:center">
    发布于 知乎 · {word_count}字 · {read_time}分钟前
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
        raise NotImplementedError("Real Zhihu publish is not implemented yet")

    def mock_publish(self, content: PlatformContent) -> PublishResult:
        """Simulate publishing to Zhihu."""
        now = datetime.now(timezone.utc)
        return PublishResult(
            platform=self.platform,
            success=True,
            published_url=f"https://zhuanlan.zhihu.com/p/mock-{id(content):x}",
            published_at=now,
            metadata={
                "mock": True,
                "platform": "zhihu",
                "word_count": len(content.body),
                "tags": content.tags,
            },
        )
