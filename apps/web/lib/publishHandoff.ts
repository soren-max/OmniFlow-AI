interface ManualPublishTextInput {
  title: string;
  content: string;
  metadata: Record<string, unknown>;
}

export interface PublishHandoffChecklist {
  titleCopied: boolean;
  bodyCopied: boolean;
  tagsCopied: boolean;
  pageOpened: boolean;
}

export const INITIAL_PUBLISH_HANDOFF_CHECKLIST: PublishHandoffChecklist = {
  titleCopied: false,
  bodyCopied: false,
  tagsCopied: false,
  pageOpened: false,
};

function toStringList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  }

  if (typeof value === "string" && value.trim().length > 0) {
    return value
      .split(/[,\s]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

export function getPreviewTags(metadata: Record<string, unknown>): string[] {
  return toStringList(metadata.hashtags ?? metadata.tags);
}

export function buildManualPublishText({ title, content, metadata }: ManualPublishTextInput): string {
  const tags = getPreviewTags(metadata);
  const summary = typeof metadata.summary === "string" ? metadata.summary : "";
  const cta = typeof metadata.cta === "string" ? metadata.cta : "";
  const notes = typeof metadata.notes === "string" ? metadata.notes : "";

  return [
    `标题：${title}`,
    "",
    "正文：",
    content,
    summary ? `\n摘要：\n${summary}` : "",
    tags.length > 0 ? `\n标签：\n${tags.map((tag) => (tag.startsWith("#") ? tag : `#${tag}`)).join(" ")}` : "",
    cta ? `\nCTA：\n${cta}` : "",
    notes ? `\n备注：\n${notes}` : "",
  ]
    .filter((section) => section.length > 0)
    .join("\n");
}
