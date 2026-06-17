"""Adapter registry — maps platform identifiers to adapter classes.

This is the central lookup point for resolving platform adapters.
Business logic should never do `if platform == "wechat"` — use the registry instead.
"""

from __future__ import annotations

from .base import PlatformAdapter
from .bilibili_adapter import BilibiliAdapter
from .douyin_adapter import DouyinAdapter
from .types import Platform
from .wechat_adapter import WeChatAdapter
from .xiaohongshu_adapter import XiaohongshuAdapter
from .zhihu_adapter import ZhihuAdapter


class AdapterNotFoundError(LookupError):
    """Raised when no adapter is registered for a given platform."""

    def __init__(self, platform: Platform | str) -> None:
        self.platform = platform
        super().__init__(f"No adapter registered for platform: {platform!r}")


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[Platform, type[PlatformAdapter]] = {
    Platform.WECHAT: WeChatAdapter,
    Platform.ZHIHU: ZhihuAdapter,
    Platform.BILIBILI: BilibiliAdapter,
    Platform.XIAOHONGSHU: XiaohongshuAdapter,
    Platform.DOUYIN: DouyinAdapter,
}


def get_adapter(platform: Platform) -> PlatformAdapter:
    """Get an adapter instance for the given platform.

    Args:
        platform: The target platform.

    Returns:
        An instantiated PlatformAdapter for the platform.

    Raises:
        AdapterNotFoundError: If no adapter is registered for the platform.
    """
    adapter_cls = _REGISTRY.get(platform)
    if adapter_cls is None:
        raise AdapterNotFoundError(platform)
    return adapter_cls()


def list_adapters() -> dict[Platform, type[PlatformAdapter]]:
    """Return a copy of the current adapter registry.

    Returns:
        A dict mapping each Platform to its adapter class.
    """
    return dict(_REGISTRY)


def register_adapter(platform: Platform, adapter_cls: type[PlatformAdapter]) -> None:
    """Register a custom adapter for a platform.

    This is useful for tests or for registering third-party adapters
    without modifying the core registry.

    Args:
        platform: The platform to register for.
        adapter_cls: The adapter class (must subclass PlatformAdapter).

    Raises:
        TypeError: If adapter_cls does not subclass PlatformAdapter.
    """
    if not issubclass(adapter_cls, PlatformAdapter):
        raise TypeError(
            f"{adapter_cls.__name__} must subclass PlatformAdapter",
        )
    _REGISTRY[platform] = adapter_cls
