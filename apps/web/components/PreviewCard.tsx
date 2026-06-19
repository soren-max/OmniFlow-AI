"use client";

import { useMemo, useState } from "react";

import {
  buildManualPublishText,
  getPreviewTags,
  INITIAL_PUBLISH_HANDOFF_CHECKLIST,
  type PublishHandoffChecklist,
} from "@/lib/publishHandoff";
import { getPublishHandoffLink } from "@/lib/publishLinks";
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
  const publishLink = getPublishHandoffLink(preview.platform);
  const [handoffChecklist, setHandoffChecklist] = useState<PublishHandoffChecklist>(
    INITIAL_PUBLISH_HANDOFF_CHECKLIST,
  );
  const [handoffStatus, setHandoffStatus] = useState<"handoff_ready" | "handoff_opened">(
    "handoff_ready",
  );
  const [handoffMessage, setHandoffMessage] = useState("");
  const [handoffError, setHandoffError] = useState("");

  const previewTags = useMemo(() => getPreviewTags(preview.metadata), [preview.metadata]);
  const copyText = useMemo(
    () =>
      buildManualPublishText({
        title: preview.title,
        content: preview.content,
        metadata: preview.metadata,
      }),
    [preview.content, preview.metadata, preview.title],
  );

  function markPageOpened() {
    setHandoffChecklist((current) => ({ ...current, pageOpened: true }));
    setHandoffStatus("handoff_opened");
    setHandoffMessage("已打开平台官方发布页，请手动粘贴、检查并确认发布。");
  }

  function openOfficialPublishPage() {
    if (!publishLink) {
      setHandoffError("当前平台暂未配置官方发布页入口。");
      return;
    }

    window.open(publishLink.officialPublishUrl, "_blank", "noopener,noreferrer");
    markPageOpened();
  }

  async function copyBeforeOpen() {
    setHandoffError("");

    try {
      if (!navigator.clipboard) {
        throw new Error("当前浏览器不支持 Clipboard API");
      }

      await navigator.clipboard.writeText(copyText);
      setHandoffChecklist({
        titleCopied: true,
        bodyCopied: true,
        tagsCopied: previewTags.length > 0,
        pageOpened: false,
      });
      setHandoffMessage("已复制标题、正文和标签，正在打开官方发布页。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "复制失败";
      setHandoffError(`复制失败：${message}。仍会打开官方发布页，请手动复制内容。`);
    } finally {
      openOfficialPublishPage();
    }
  }

  const checklistItems = [
    { label: "标题已复制", done: handoffChecklist.titleCopied },
    { label: "正文已复制", done: handoffChecklist.bodyCopied },
    { label: "标签已复制", done: handoffChecklist.tagsCopied || previewTags.length === 0 },
    { label: "已打开发布页", done: handoffChecklist.pageOpened },
    { label: "需要人工确认提交", done: true },
  ];

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

      {/* Manual publish handoff */}
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4 dark:border-slate-800 dark:bg-slate-900/70">
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Official publish handoff
              </p>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                将打开平台官方发布页，你仍需要手动粘贴、检查并确认发布。
              </p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                This opens the official publishing page. You still need to review and submit
                manually.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300">
                {handoffStatus === "handoff_opened" ? "handoff_opened" : "handoff_ready"}
              </span>
              <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
                {publishLink?.status ?? "manual_publish_required"}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={openOfficialPublishPage}
              disabled={!publishLink}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
            >
              打开发布页
            </button>
            <button
              type="button"
              onClick={copyBeforeOpen}
              disabled={!publishLink}
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-slate-300"
            >
              复制后打开
            </button>
          </div>

          <div className="grid gap-2 text-xs text-slate-600 dark:text-slate-300 sm:grid-cols-2">
            {checklistItems.map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <span
                  className={
                    item.done
                      ? "h-2 w-2 rounded-full bg-emerald-500"
                      : "h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-700"
                  }
                />
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          {handoffMessage && (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300">
              {handoffMessage}
            </p>
          )}
          {handoffError && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
              {handoffError}
            </p>
          )}
        </div>
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
