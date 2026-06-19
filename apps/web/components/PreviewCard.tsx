"use client";

import { useMemo, useState } from "react";
import type { ProjectPreviewItem } from "@/types";
import { PLATFORM_OPTIONS } from "@/types";

interface PreviewCardProps {
  preview: ProjectPreviewItem;
}

/**
 * Displays a single platform preview result.
 * Shows rendered HTML, metadata, and any validation warnings.
 */
export function PreviewCard({ preview }: PreviewCardProps) {
  const platformInfo = PLATFORM_OPTIONS.find((p) => p.id === preview.platform);
  const [copyStatus, setCopyStatus] = useState("");
  const [copyError, setCopyError] = useState("");

  const hashtags = useMemo(() => {
    const rawTags = preview.metadata.hashtags ?? preview.metadata.tags;
    return Array.isArray(rawTags)
      ? rawTags.map((tag) => String(tag)).filter((tag) => tag.trim().length > 0)
      : [];
  }, [preview.metadata]);

  const cta = typeof preview.metadata.call_to_action === "string" ? preview.metadata.call_to_action : "";
  const copyText = [preview.title, "", preview.content, "", hashtags.map((tag) => `#${tag}`).join(" "), cta]
    .filter((part) => part.trim().length > 0)
    .join("\n");

  async function copyToClipboard(label: string, value: string): Promise<void> {
    setCopyStatus("");
    setCopyError("");
    if (!navigator.clipboard) {
      setCopyError("当前浏览器不支持 Clipboard API");
      return;
    }
    try {
      await navigator.clipboard.writeText(value);
      setCopyStatus(`${label}已复制`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "复制失败";
      setCopyError(message);
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
      {/* Platform header */}
      <div
        className="flex items-center justify-between px-5 py-3 text-white"
        style={{ backgroundColor: platformInfo?.color ?? "#6366f1" }}
      >
        <span className="text-sm font-semibold">{preview.platform_display_name}</span>
        <span className="rounded-full bg-white/15 px-2 py-0.5 text-xs font-medium opacity-95">
          {preview.word_count} 字 · 约{preview.estimated_read_time_min}分钟
        </span>
      </div>

      {/* Warnings */}
      {preview.warnings.length > 0 && (
        <div className="border-b border-amber-100 bg-amber-50 px-5 py-2 text-xs text-amber-700 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-400">
          {preview.warnings.map((w, i) => (
            <p key={i}>⚠ {w}</p>
          ))}
        </div>
      )}

      <div className="border-b border-slate-200 bg-white px-5 py-3 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void copyToClipboard("内容", copyText)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
          >
            复制内容
          </button>
          <button
            type="button"
            onClick={() => void copyToClipboard("标题", preview.title)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
          >
            复制标题
          </button>
          <button
            type="button"
            onClick={() => void copyToClipboard("标签", hashtags.join(" "))}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
          >
            复制标签
          </button>
        </div>
        {(copyStatus || copyError) && (
          <p
            className={`mt-2 text-xs ${
              copyError ? "text-red-600 dark:text-red-400" : "text-green-700 dark:text-green-300"
            }`}
          >
            {copyError || copyStatus}
          </p>
        )}
      </div>

      {/* Rendered preview */}
      <div className="max-h-[520px] overflow-y-auto bg-slate-50 p-2 dark:bg-slate-900">
        <div
          className="preview-content rounded-xl bg-white shadow-sm ring-1 ring-slate-100 [&_img]:max-w-full [&_table]:w-full dark:bg-slate-950 dark:ring-slate-800"
          dangerouslySetInnerHTML={{ __html: preview.rendered_html }}
        />
      </div>
    </div>
  );
}
