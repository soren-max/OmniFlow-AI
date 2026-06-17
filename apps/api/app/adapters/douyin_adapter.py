"""Douyin platform adapter.

Douyin (抖音) content style:
- Short-video first, with a strong opening hook.
- Conversational spoken script and fast pacing.
- Simple shot list for video production.
- Tags and call-to-action for discovery and engagement.
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

_TITLE_MAX_LENGTH = 55
_SCRIPT_MAX_LENGTH = 800
_MIN_TAGS = 2
_MAX_TAGS = 8
_DEFAULT_TAGS = ["AI工具", "内容运营", "效率提升"]
_DEFAULT_CTA = "你更想看哪个平台的版本? 评论区告诉我。"


class DouyinAdapter(PlatformAdapter):
    """Adapter for Douyin short-video content."""

    platform = Platform.DOUYIN

    @property
    def platform_name(self) -> str:
        return "Douyin"

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against Douyin short-video guidance."""
        errors: list[str] = []
        warnings: list[str] = []

        if len(content.title) > _TITLE_MAX_LENGTH:
            warnings.append(
                f"Title exceeds recommended {_TITLE_MAX_LENGTH} characters "
                f"(got {len(content.title)}). Douyin titles work best when concise.",
            )

        if len(content.body.strip()) > _SCRIPT_MAX_LENGTH:
            warnings.append(
                f"Script is long for a short video ({len(content.body.strip())} chars). "
                "Consider tightening the pacing.",
            )

        if len(content.tags) < _MIN_TAGS:
            warnings.append(
                f"At least {_MIN_TAGS} tags recommended for Douyin discoverability "
                f"(got {len(content.tags)})",
            )
        if len(content.tags) > _MAX_TAGS:
            errors.append(f"Maximum {_MAX_TAGS} tags allowed on Douyin")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def transform_content(self, content: PlatformContent) -> PlatformContent:
        """Transform source content into a Douyin short-video script."""
        clean_body = re.sub(r"\s+", " ", content.body).strip()
        source_excerpt = clean_body[:220].rstrip()
        hook = content.hooks[0] if content.hooks else f"3秒看懂: {content.title}"
        script = (
            f"{hook}\n\n"
            f"今天用一个短视频讲清楚: {source_excerpt}"
            f"{'...' if len(clean_body) > len(source_excerpt) else ''}\n\n"
            f"最后记住一个重点: 把内容拆成平台适配、预览检查和人工确认三步。"
        )
        shot_list = [
            "镜头 1: 开场吸引, 直接抛出痛点或结果",
            "镜头 2: 展示核心内容, 用字幕强调关键步骤",
            "镜头 3: 总结价值, 并引导评论互动",
        ]
        douyin_tags = [tag.replace(" ", "") for tag in (content.tags or _DEFAULT_TAGS)]

        body_html = f"""\
<div class="douyin-video-script">
  <p><strong>前 3 秒 Hook:</strong>{html.escape(hook)}</p>
  <p><strong>口播脚本:</strong>{html.escape(script)}</p>
  <ol>
    {"".join(f"<li>{html.escape(shot)}</li>" for shot in shot_list)}
  </ol>
  <p><strong>互动引导:</strong>{html.escape(_DEFAULT_CTA)}</p>
</div>"""

        return content.model_copy(
            update={
                "title": content.title[:_TITLE_MAX_LENGTH],
                "body": body_html,
                "hooks": [hook],
                "tags": douyin_tags,
                "summary": content.summary or "抖音短视频脚本、前三秒 Hook、分镜建议和互动引导",
                "metadata": {
                    **content.metadata,
                    "format": "douyin_short_video_script",
                    "hook": hook,
                    "script": script,
                    "shot_list": shot_list,
                    "call_to_action": _DEFAULT_CTA,
                },
            }
        )

    def build_preview(self, content: PlatformContent) -> PreviewResult:
        """Build a Douyin-style short-video preview."""
        word_count = len(content.body.replace("<", "").replace(">", ""))
        read_time = max(1, round(word_count / 220))
        tags_html = " ".join(
            f'<span style="color:#00f2ea;font-size:12px;margin-right:8px">#{html.escape(t)}</span>'
            for t in content.tags
        )
        rendered = f"""\
<div style="max-width:420px;margin:0 auto;background:#111;color:#f7f7f7;font-family:-apple-system,'PingFang SC',sans-serif;border-radius:10px;overflow:hidden">
  <div style="min-height:220px;background:#1f1f1f;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center">
    <div>
      <div style="font-size:12px;color:#00f2ea;margin-bottom:10px">Douyin Short Video Preview</div>
      <h1 style="font-size:20px;line-height:1.35;margin:0">{html.escape(content.title)}</h1>
    </div>
  </div>
  <div style="padding:16px">
    <div style="font-size:13px;line-height:1.7;color:#f1f1f1">{content.body}</div>
    <div style="margin-top:12px">{tags_html}</div>
    <div style="margin-top:16px;padding-top:12px;border-top:1px solid #333;color:#aaa;font-size:12px">
      抖音 · {word_count}字脚本 · Mock preview
    </div>
  </div>
</div>"""
        return PreviewResult(
            platform=self.platform,
            rendered_html=rendered,
            word_count=word_count,
            estimated_read_time_min=read_time,
            metadata={
                "hook": content.metadata.get("hook"),
                "shot_list": content.metadata.get("shot_list", []),
                "call_to_action": content.metadata.get("call_to_action"),
            },
        )

    def publish(self, content: PlatformContent) -> PublishResult:
        """Real publish — not implemented in mock stage."""
        raise NotImplementedError("Real Douyin publish is not implemented yet")

    def mock_publish(self, content: PlatformContent) -> PublishResult:
        """Simulate publishing to Douyin."""
        now = datetime.now(timezone.utc)
        mock_id = f"mock-{id(content):x}"
        return PublishResult(
            platform=self.platform,
            success=True,
            published_url=f"mock://douyin/post/{mock_id}",
            published_at=now,
            metadata={
                "mock": True,
                "platform": "douyin",
                "post_id": mock_id,
                "message": "Mock published to Douyin successfully.",
            },
        )
