"""Platform-specific publishing adapters.

Current stage: Concrete mock adapters implemented for all 5 platforms.
- PlatformAdapter abstract base class in base.py
- Shared data types in types.py
- Mock adapters: WeChatAdapter, ZhihuAdapter, BilibiliAdapter, XiaohongshuAdapter, DouyinAdapter
- Adapter registry for platform → class resolution

Future stages:
- Real platform API integration with authentication.
- Publishing workflows via service layer.
"""

from .base import PlatformAdapter
from .bilibili_adapter import BilibiliAdapter
from .douyin_adapter import DouyinAdapter
from .registry import AdapterNotFoundError, get_adapter, list_adapters, register_adapter
from .types import (
    Platform,
    PlatformContent,
    PreviewResult,
    PublishResult,
    ValidationResult,
)
from .wechat_adapter import WeChatAdapter
from .xiaohongshu_adapter import XiaohongshuAdapter
from .zhihu_adapter import ZhihuAdapter

__all__ = [
    "AdapterNotFoundError",
    "BilibiliAdapter",
    "DouyinAdapter",
    "Platform",
    "PlatformAdapter",
    "PlatformContent",
    "PreviewResult",
    "PublishResult",
    "ValidationResult",
    "WeChatAdapter",
    "XiaohongshuAdapter",
    "ZhihuAdapter",
    "get_adapter",
    "list_adapters",
    "register_adapter",
]
