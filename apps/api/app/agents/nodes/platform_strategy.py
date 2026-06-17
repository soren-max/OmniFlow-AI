"""Platform strategy node for the content preview workflow."""

from __future__ import annotations

from api.app.agents.state import ContentWorkflowState

PLATFORM_STRATEGIES: dict[str, str] = {
    "wechat": "long-form article",
    "zhihu": "analytical answer",
    "bilibili": "video script",
    "xiaohongshu": "lifestyle note",
    "douyin": "short video script",
}


def platform_strategy_node(state: ContentWorkflowState) -> ContentWorkflowState:
    """Create deterministic platform strategies for requested platforms."""
    if state["errors"]:
        return state

    strategies = {
        platform: {
            "format": PLATFORM_STRATEGIES.get(platform, "generic content preview"),
            "deterministic": True,
        }
        for platform in state["target_platforms"]
    }

    return {
        **state,
        "platform_strategy": strategies,
        "status": "strategy_ready",
    }
