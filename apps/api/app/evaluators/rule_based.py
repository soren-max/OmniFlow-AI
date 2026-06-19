"""Rule-based content quality evaluation for platform previews."""

from __future__ import annotations

from typing import Any

from api.app.adapters.types import Platform

PLATFORM_STYLE_KEYS: dict[str, tuple[str, ...]] = {
    Platform.WECHAT.value: ("format", "summary"),
    Platform.ZHIHU.value: ("format", "summary"),
    Platform.BILIBILI.value: ("script_outline", "call_to_action"),
    Platform.XIAOHONGSHU.value: ("hashtags", "emoji_style"),
    Platform.DOUYIN.value: ("shot_list", "call_to_action"),
}


def evaluate_project_previews(project: dict[str, Any]) -> dict[str, Any]:
    """Evaluate persisted platform previews with deterministic rules."""
    previews = [
        preview
        for preview in project.get("previews", [])
        if isinstance(preview, dict) and preview.get("platform")
    ]
    platform_scores = [_evaluate_preview(project, preview) for preview in previews]
    average_score = _average([score["overall_score"] for score in platform_scores])
    issues = _unique(
        issue for score in platform_scores for issue in list(score.get("issues", []))
    )
    suggestions = _unique(
        suggestion
        for score in platform_scores
        for suggestion in list(score.get("suggestions", []))
    )

    return {
        "project_id": str(project["id"]),
        "average_score": average_score,
        "platform_scores": platform_scores,
        "issues": issues,
        "suggestions": suggestions,
    }


def _evaluate_preview(project: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    platform = str(preview["platform"])
    title = str(preview.get("title") or "")
    content = str(preview.get("content") or "")
    rendered_html = str(preview.get("rendered_html") or "")
    metadata = _dict_value(preview.get("metadata"))
    validation = _dict_value(preview.get("validation"))
    warnings = list(preview.get("warnings", []))
    validation_errors = list(validation.get("errors", []))
    validation_warnings = list(validation.get("warnings", []))
    all_warnings = [str(item) for item in [*warnings, *validation_warnings]]

    issues: list[str] = []
    suggestions: list[str] = []

    format_score = 100
    if not rendered_html:
        format_score -= 35
        issues.append(f"{platform}: missing rendered preview HTML")
    if not title:
        format_score -= 25
        issues.append(f"{platform}: missing title")
    if len(content) < 80:
        format_score -= 20
        suggestions.append(f"{platform}: expand adapted content for a fuller preview")

    style_score = 100
    missing_style_keys = [
        key for key in PLATFORM_STYLE_KEYS.get(platform, ()) if not metadata.get(key)
    ]
    if missing_style_keys:
        style_score -= 12 * len(missing_style_keys)
        suggestions.append(
            f"{platform}: add platform style metadata: {', '.join(missing_style_keys)}"
        )
    if not metadata.get("tags") and not metadata.get("hashtags"):
        style_score -= 10
        suggestions.append(f"{platform}: add platform-specific tags or hashtags")

    consistency_score = 100
    source_title = str(project.get("title") or "")
    source_text = str(project.get("source_text") or "")
    if source_title and source_title.lower() not in f"{title} {content}".lower():
        consistency_score -= 18
        suggestions.append(f"{platform}: make the adapted title/content reflect the source title")
    if source_text and _word_overlap(source_text, content) < 0.08:
        consistency_score -= 22
        issues.append(f"{platform}: adapted content appears weakly connected to source text")

    compliance_score = 100
    if validation_errors:
        compliance_score -= min(60, 25 * len(validation_errors))
        issues.extend(f"{platform}: {error}" for error in validation_errors)
    if all_warnings:
        compliance_score -= min(25, 8 * len(all_warnings))
        suggestions.extend(f"{platform}: {warning}" for warning in all_warnings)

    completeness_score = 100
    if not metadata.get("summary"):
        completeness_score -= 15
        suggestions.append(f"{platform}: add a concise summary")
    if not metadata.get("hooks"):
        completeness_score -= 15
        suggestions.append(f"{platform}: add an opening hook")
    if int(preview.get("word_count", 0)) <= 0:
        completeness_score -= 20
        issues.append(f"{platform}: word count was not recorded")

    scores = {
        "format_score": _clamp(format_score),
        "style_score": _clamp(style_score),
        "consistency_score": _clamp(consistency_score),
        "compliance_score": _clamp(compliance_score),
        "completeness_score": _clamp(completeness_score),
    }
    overall_score = _average(list(scores.values()))

    return {
        "platform": platform,
        "platform_display_name": str(preview.get("platform_display_name") or platform),
        **scores,
        "overall_score": overall_score,
        "issues": _unique(issues),
        "suggestions": _unique(suggestions),
    }


def _dict_value(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _word_overlap(source: str, adapted: str) -> float:
    source_words = _words(source)
    adapted_words = _words(adapted)
    if not source_words or not adapted_words:
        return 0.0
    return len(source_words & adapted_words) / len(source_words)


def _words(value: str) -> set[str]:
    return {word.lower() for word in value.split() if len(word) > 3}


def _average(scores: list[int]) -> int:
    if not scores:
        return 0
    return round(sum(scores) / len(scores))


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
