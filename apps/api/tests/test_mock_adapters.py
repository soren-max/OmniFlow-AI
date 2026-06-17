"""Tests for the concrete mock platform adapters and the adapter registry.

Each platform adapter is tested for:
- validate_content (valid / invalid cases)
- transform_content (format changes)
- build_preview (returns PreviewResult)
- mock_publish (returns successful PublishResult with mock URL)
- publish (raises NotImplementedError)
"""

from __future__ import annotations

import pytest
from api.app.adapters.base import PlatformAdapter  # type: ignore[import-untyped]
from api.app.adapters.bilibili_adapter import BilibiliAdapter  # type: ignore[import-untyped]
from api.app.adapters.douyin_adapter import DouyinAdapter  # type: ignore[import-untyped]
from api.app.adapters.registry import (  # type: ignore[import-untyped]
    AdapterNotFoundError,
    get_adapter,
    list_adapters,
    register_adapter,
)
from api.app.adapters.types import (  # type: ignore[import-untyped]
    Platform,
    PlatformContent,
    PreviewResult,
    PublishResult,
    ValidationResult,
)
from api.app.adapters.wechat_adapter import WeChatAdapter  # type: ignore[import-untyped]
from api.app.adapters.xiaohongshu_adapter import XiaohongshuAdapter  # type: ignore[import-untyped]
from api.app.adapters.zhihu_adapter import ZhihuAdapter  # type: ignore[import-untyped]

# ── Shared fixture ────────────────────────────────────────────────────────────

SAMPLE_BODY = (
    "This is a sample article body that should be long enough "
    "to pass minimum length validation on all platforms. "
    "It contains enough content to produce meaningful transformations.\n\n"
    "# Section One\n\n"
    "This is the first section with detailed analysis. "
    "We cover important points and provide insights.\n\n"
    "## Sub section\n\n"
    "More detailed content here with specific examples.\n\n"
    "- List item one\n"
    "- List item two\n"
    "- List item three\n\n"
    "> A meaningful quote to highlight.\n\n"
    "## Conclusion\n\n"
    "Final thoughts and wrap up of this comprehensive article."
)


@pytest.fixture
def sample_content() -> PlatformContent:
    """Create a reusable sample PlatformContent."""
    return PlatformContent(
        platform=Platform.WECHAT,  # Will be overridden by adapter
        title="Test Article Title for Platform Adapters",
        body=SAMPLE_BODY,
        summary="A test article for validating platform adapters",
        hooks=["Did you know that..."],
        tags=["testing", "platform", "adapters"],
        cover_image_url="https://example.com/cover.jpg",
    )


def _make_content(
    platform: Platform,
    title: str = "Test Title",
    body: str = SAMPLE_BODY,
    tags: list[str] | None = None,
    **kwargs: object,
) -> PlatformContent:
    """Helper to create PlatformContent with overrides."""
    resolved_tags = tags if tags is not None else ["tag1", "tag2", "tag3"]
    return PlatformContent(
        platform=platform,
        title=title,
        body=body,
        tags=resolved_tags,
        **kwargs,
    )


# ── WeChat Adapter ────────────────────────────────────────────────────────────


class TestWeChatAdapter:
    @pytest.fixture
    def adapter(self) -> WeChatAdapter:
        return WeChatAdapter()

    def test_platform_name(self, adapter: WeChatAdapter) -> None:
        assert adapter.platform_name == "WeChat Official Accounts"

    def test_validate_valid(self, adapter: WeChatAdapter) -> None:
        result = adapter.validate_content(_make_content(Platform.WECHAT))
        assert result.is_valid is True
        assert result.has_errors is False

    def test_validate_title_too_long(self, adapter: WeChatAdapter) -> None:
        content = _make_content(Platform.WECHAT, title="A" * 65)
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("64" in e for e in result.errors)

    def test_validate_body_too_short(self, adapter: WeChatAdapter) -> None:
        content = _make_content(Platform.WECHAT, body="Short")
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_missing_cover_warning(self, adapter: WeChatAdapter) -> None:
        content = _make_content(Platform.WECHAT, cover_image_url=None)
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert any("cover" in w.lower() for w in result.warnings)

    def test_transform_content(self, adapter: WeChatAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        transformed = adapter.transform_content(sample_content)
        assert "<section" in transformed.body
        assert "wechat-article" in transformed.body
        assert "<p>" in transformed.body
        assert "<h2>" in transformed.body
        assert transformed.metadata.get("format") == "wechat_rich_text"

    def test_build_preview(self, adapter: WeChatAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        preview = adapter.build_preview(sample_content)
        assert isinstance(preview, PreviewResult)
        assert preview.platform == Platform.WECHAT
        assert "WeChat" in preview.rendered_html
        assert preview.word_count > 0
        assert preview.estimated_read_time_min >= 1

    def test_mock_publish(self, adapter: WeChatAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        result = adapter.mock_publish(sample_content)
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert result.is_published is True
        assert "mp.weixin.qq.com" in (result.published_url or "")
        assert result.metadata.get("mock") is True

    def test_publish_not_implemented(self, adapter: WeChatAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        with pytest.raises(NotImplementedError, match="WeChat"):
            adapter.publish(sample_content)


# ── Zhihu Adapter ─────────────────────────────────────────────────────────────


class TestZhihuAdapter:
    @pytest.fixture
    def adapter(self) -> ZhihuAdapter:
        return ZhihuAdapter()

    def test_platform_name(self, adapter: ZhihuAdapter) -> None:
        assert adapter.platform_name == "Zhihu"

    def test_validate_valid(self, adapter: ZhihuAdapter) -> None:
        result = adapter.validate_content(_make_content(Platform.ZHIHU))
        assert result.is_valid is True

    def test_validate_title_too_long(self, adapter: ZhihuAdapter) -> None:
        content = _make_content(Platform.ZHIHU, title="A" * 81)
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_no_tags(self, adapter: ZhihuAdapter) -> None:
        content = _make_content(Platform.ZHIHU, tags=[])
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("tag" in e.lower() for e in result.errors)

    def test_validate_too_many_tags(self, adapter: ZhihuAdapter) -> None:
        content = _make_content(Platform.ZHIHU, tags=[f"tag{i}" for i in range(6)])
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_transform_content(self, adapter: ZhihuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        transformed = adapter.transform_content(sample_content)
        assert "<article" in transformed.body
        assert "zh-article" in transformed.body
        assert "zh-intro" in transformed.body
        assert "zh-conclusion" in transformed.body
        assert transformed.metadata.get("format") == "zhihu_article"

    def test_build_preview(self, adapter: ZhihuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        preview = adapter.build_preview(sample_content)
        assert isinstance(preview, PreviewResult)
        assert preview.platform == Platform.ZHIHU
        assert "zhihu" in preview.rendered_html.lower() or "知乎" in preview.rendered_html

    def test_mock_publish(self, adapter: ZhihuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        result = adapter.mock_publish(sample_content)
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert "zhuanlan.zhihu.com" in (result.published_url or "")
        assert result.metadata.get("mock") is True

    def test_publish_not_implemented(self, adapter: ZhihuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        with pytest.raises(NotImplementedError, match="Zhihu"):
            adapter.publish(sample_content)


# ── Bilibili Adapter ──────────────────────────────────────────────────────────


class TestBilibiliAdapter:
    @pytest.fixture
    def adapter(self) -> BilibiliAdapter:
        return BilibiliAdapter()

    def test_platform_name(self, adapter: BilibiliAdapter) -> None:
        assert adapter.platform_name == "Bilibili"

    def test_validate_valid(self, adapter: BilibiliAdapter) -> None:
        result = adapter.validate_content(_make_content(Platform.BILIBILI))
        assert result.is_valid is True

    def test_validate_title_too_long(self, adapter: BilibiliAdapter) -> None:
        content = _make_content(Platform.BILIBILI, title="A" * 81)
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_too_many_tags(self, adapter: BilibiliAdapter) -> None:
        content = _make_content(Platform.BILIBILI, tags=[f"t{i}" for i in range(11)])
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_short_body_warning(self, adapter: BilibiliAdapter) -> None:
        content = _make_content(Platform.BILIBILI, body="Hi")
        result = adapter.validate_content(content)
        assert result.is_valid is True  # Warning only, not an error
        assert len(result.warnings) > 0

    def test_transform_content(self, adapter: BilibiliAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        transformed = adapter.transform_content(sample_content)
        assert "bilibili-script" in transformed.body
        assert "bilibili-opening" in transformed.body
        assert "bilibili-cta" in transformed.body
        assert any(t.startswith("#") for t in transformed.tags)
        assert transformed.metadata.get("format") == "bilibili_video_script"

    def test_build_preview(self, adapter: BilibiliAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        preview = adapter.build_preview(sample_content)
        assert isinstance(preview, PreviewResult)
        assert preview.platform == Platform.BILIBILI
        assert "Bilibili" in preview.rendered_html

    def test_mock_publish(self, adapter: BilibiliAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        result = adapter.mock_publish(sample_content)
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert "bilibili.com" in (result.published_url or "")
        assert result.metadata.get("video_id") is not None

    def test_publish_not_implemented(self, adapter: BilibiliAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        with pytest.raises(NotImplementedError, match="Bilibili"):
            adapter.publish(sample_content)


# ── Xiaohongshu Adapter ───────────────────────────────────────────────────────


class TestXiaohongshuAdapter:
    @pytest.fixture
    def adapter(self) -> XiaohongshuAdapter:
        return XiaohongshuAdapter()

    def test_platform_name(self, adapter: XiaohongshuAdapter) -> None:
        assert adapter.platform_name == "Xiaohongshu (RED)"

    def test_validate_valid(self, adapter: XiaohongshuAdapter) -> None:
        content = _make_content(Platform.XIAOHONGSHU, body="A" * 500)
        result = adapter.validate_content(content)
        assert result.is_valid is True

    def test_validate_body_too_long(self, adapter: XiaohongshuAdapter) -> None:
        content = _make_content(Platform.XIAOHONGSHU, body="A" * 1001)
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("1000" in e for e in result.errors)

    def test_validate_no_tags_warning(self, adapter: XiaohongshuAdapter) -> None:
        content = _make_content(Platform.XIAOHONGSHU, tags=[])
        result = adapter.validate_content(content)
        assert result.is_valid is True  # Warning only
        assert len(result.warnings) > 0

    def test_transform_content(self, adapter: XiaohongshuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        transformed = adapter.transform_content(sample_content)
        assert "xhs-post" in transformed.body
        assert "✨" in transformed.title or len(transformed.title) > 0
        assert any(t.startswith("#") for t in transformed.tags)
        assert transformed.metadata.get("format") == "xiaohongshu_post"
        assert transformed.metadata.get("emoji_style") is True

    def test_build_preview(self, adapter: XiaohongshuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        preview = adapter.build_preview(sample_content)
        assert isinstance(preview, PreviewResult)
        assert preview.platform == Platform.XIAOHONGSHU
        assert "❤️" in preview.rendered_html or "小红书" in preview.rendered_html

    def test_mock_publish(self, adapter: XiaohongshuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        result = adapter.mock_publish(sample_content)
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert "xiaohongshu.com" in (result.published_url or "")
        assert result.metadata.get("note_id") is not None

    def test_publish_not_implemented(self, adapter: XiaohongshuAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        with pytest.raises(NotImplementedError, match="Xiaohongshu"):
            adapter.publish(sample_content)


# ── Douyin Adapter ────────────────────────────────────────────────────────────


class TestDouyinAdapter:
    @pytest.fixture
    def adapter(self) -> DouyinAdapter:
        return DouyinAdapter()

    def test_platform_name(self, adapter: DouyinAdapter) -> None:
        assert adapter.platform_name == "Douyin"

    def test_validate_valid(self, adapter: DouyinAdapter) -> None:
        result = adapter.validate_content(_make_content(Platform.DOUYIN))
        assert result.is_valid is True

    def test_validate_too_many_tags(self, adapter: DouyinAdapter) -> None:
        content = _make_content(Platform.DOUYIN, tags=[f"t{i}" for i in range(9)])
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("8" in e for e in result.errors)

    def test_validate_long_title_warning(self, adapter: DouyinAdapter) -> None:
        content = _make_content(Platform.DOUYIN, title="A" * 56)
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert any("Title" in w for w in result.warnings)

    def test_transform_content(self, adapter: DouyinAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        content = sample_content.model_copy(update={"platform": Platform.DOUYIN})
        transformed = adapter.transform_content(content)
        assert "douyin-video-script" in transformed.body
        assert "前 3 秒 Hook" in transformed.body
        assert transformed.hooks
        assert transformed.metadata.get("format") == "douyin_short_video_script"
        assert transformed.metadata.get("shot_list")
        assert transformed.metadata.get("call_to_action")

    def test_build_preview(self, adapter: DouyinAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        content = sample_content.model_copy(update={"platform": Platform.DOUYIN})
        transformed = adapter.transform_content(content)
        preview = adapter.build_preview(transformed)
        assert isinstance(preview, PreviewResult)
        assert preview.platform == Platform.DOUYIN
        assert "Douyin Short Video Preview" in preview.rendered_html
        assert preview.metadata.get("shot_list")

    def test_mock_publish(self, adapter: DouyinAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        content = sample_content.model_copy(update={"platform": Platform.DOUYIN})
        result = adapter.mock_publish(content)
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert "mock://douyin/post/" in (result.published_url or "")
        assert result.metadata.get("message") == "Mock published to Douyin successfully."

    def test_publish_not_implemented(self, adapter: DouyinAdapter, sample_content: PlatformContent) -> None:  # fmt: skip
        with pytest.raises(NotImplementedError, match="Douyin"):
            adapter.publish(sample_content)


# ── Adapter Registry ──────────────────────────────────────────────────────────


class TestAdapterRegistry:
    def test_get_wechat_adapter(self) -> None:
        adapter = get_adapter(Platform.WECHAT)
        assert isinstance(adapter, WeChatAdapter)

    def test_get_zhihu_adapter(self) -> None:
        adapter = get_adapter(Platform.ZHIHU)
        assert isinstance(adapter, ZhihuAdapter)

    def test_get_bilibili_adapter(self) -> None:
        adapter = get_adapter(Platform.BILIBILI)
        assert isinstance(adapter, BilibiliAdapter)

    def test_get_xiaohongshu_adapter(self) -> None:
        adapter = get_adapter(Platform.XIAOHONGSHU)
        assert isinstance(adapter, XiaohongshuAdapter)

    def test_get_douyin_adapter(self) -> None:
        adapter = get_adapter(Platform.DOUYIN)
        assert isinstance(adapter, DouyinAdapter)

    def test_get_adapter_returns_new_instance(self) -> None:
        a1 = get_adapter(Platform.WECHAT)
        a2 = get_adapter(Platform.WECHAT)
        assert a1 is not a2  # Different instances

    def test_get_adapter_not_found(self) -> None:
        """Registry should raise AdapterNotFoundError for unknown platforms."""
        # Temporarily remove WeChat from the registry to test not-found path
        from api.app.adapters.registry import _REGISTRY

        original = _REGISTRY.pop(Platform.WECHAT)
        try:
            with pytest.raises(AdapterNotFoundError, match="wechat"):
                get_adapter(Platform.WECHAT)
        finally:
            _REGISTRY[Platform.WECHAT] = original

    def test_list_adapters_returns_all_platforms(self) -> None:
        adapters = list_adapters()
        assert set(adapters.keys()) == {
            Platform.WECHAT,
            Platform.ZHIHU,
            Platform.BILIBILI,
            Platform.XIAOHONGSHU,
            Platform.DOUYIN,
        }

    def test_list_adapters_returns_copy(self) -> None:
        adapters = list_adapters()
        adapters.clear()
        # Original registry should not be affected
        assert len(list_adapters()) == 5

    def test_register_adapter_custom(self) -> None:
        """Registering a custom adapter should override the existing one."""

        class CustomWeChatAdapter(WeChatAdapter):  # type: ignore[misc]
            @property
            def platform_name(self) -> str:
                return "Custom WeChat"

        register_adapter(Platform.WECHAT, CustomWeChatAdapter)
        adapter = get_adapter(Platform.WECHAT)
        assert isinstance(adapter, CustomWeChatAdapter)
        assert adapter.platform_name == "Custom WeChat"

        # Restore original
        register_adapter(Platform.WECHAT, WeChatAdapter)

    def test_register_adapter_invalid_type(self) -> None:
        """Registering a non-PlatformAdapter subclass should raise TypeError."""

        class NotAnAdapter:
            pass

        with pytest.raises(TypeError, match="PlatformAdapter"):
            register_adapter(Platform.WECHAT, NotAnAdapter)

    def test_all_adapters_satisfy_interface(self) -> None:
        """Every adapter in the registry should implement PlatformAdapter."""
        for platform, adapter_cls in list_adapters().items():
            adapter = adapter_cls()
            assert isinstance(adapter, PlatformAdapter)
            # Smoke test every required method
            content = PlatformContent(
                platform=platform,
                title="Test",
                body="Body content " * 20,
                tags=["a", "b", "c"],
            )
            assert isinstance(adapter.validate_content(content), ValidationResult)
            transformed = adapter.transform_content(content)
            assert isinstance(transformed, PlatformContent)
            assert isinstance(adapter.build_preview(transformed), PreviewResult)
            result = adapter.mock_publish(transformed)
            assert isinstance(result, PublishResult)
            assert result.success is True
            # publish() must raise NotImplementedError
            with pytest.raises(NotImplementedError):
                adapter.publish(transformed)
