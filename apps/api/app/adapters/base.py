"""Abstract base class for platform-specific adapters.

All platform adapters must inherit from PlatformAdapter and implement
the required methods. This ensures a consistent interface regardless
of the target platform's API specifics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .types import (
    Platform,
    PlatformContent,
    PreviewResult,
    PublishResult,
    ValidationResult,
)


class PlatformAdapter(ABC):
    """Abstract interface for platform content adapters.

    Each supported platform (WeChat, Zhihu, Bilibili, Xiaohongshu, Douyin)
    must implement a concrete subclass that provides platform-specific
    validation, transformation, preview, and publishing logic.
    """

    platform: Platform
    """The platform this adapter targets."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name, e.g. 'WeChat Official Accounts'."""
        ...

    @abstractmethod
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against platform-specific rules.

        Checks may include:
        - Title length limits.
        - Body content restrictions (e.g. no external links).
        - Media requirements (e.g. cover image required).
        - Format compliance (e.g. Markdown vs rich text).

        Args:
            content: The platform-adapted content to validate.

        Returns:
            A ValidationResult indicating pass/fail with error details.
        """
        ...

    @abstractmethod
    def transform_content(self, content: PlatformContent) -> PlatformContent:
        """Transform content into the platform's native format.

        Transformations may include:
        - Converting Markdown to platform-specific rich text.
        - Resizing or reformatting images.
        - Restructuring sections for platform layout.

        Args:
            content: The source content to transform.

        Returns:
            The transformed PlatformContent ready for preview or publish.
        """
        ...

    @abstractmethod
    def build_preview(self, content: PlatformContent) -> PreviewResult:
        """Generate a visual preview of how content will appear on the platform.

        Args:
            content: The transformed platform content.

        Returns:
            A PreviewResult with rendered HTML and metadata.
        """
        ...

    @abstractmethod
    def publish(self, content: PlatformContent) -> PublishResult:
        """Publish content to the real platform API.

        WARNING: This method is reserved for future stages.
        In the current bootstrap stage, only mock_publish is implemented.

        Args:
            content: The final platform-ready content.

        Returns:
            A PublishResult indicating success/failure.
        """
        ...

    @abstractmethod
    def mock_publish(self, content: PlatformContent) -> PublishResult:
        """Simulate publishing without calling a real platform API.

        Used for testing and demonstration. Records what *would* have
        been published without sending data to an external service.

        Args:
            content: The final platform-ready content.

        Returns:
            A PublishResult simulating a successful publish.
        """
        ...
