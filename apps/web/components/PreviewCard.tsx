"use client";

import { useMemo, useState } from "react";

import {
  buildManualPublishText,
  getPreviewTags,
  INITIAL_PUBLISH_HANDOFF_CHECKLIST,
  type PublishHandoffChecklist,
} from "@/lib/publishHandoff";
import { api, getErrorMessage } from "@/lib/api";
import { getPublishHandoffLink, HANDOFF_STATUS_LABELS } from "@/lib/publishLinks";
import type { ProjectPreviewItem, PublishDraft } from "@/types";
import { PLATFORM_OPTIONS } from "@/types";

interface PreviewCardProps {
  preview: ProjectPreviewItem;
  projectId: string;
  onDraftSaved?: (draft: PublishDraft) => void;
}

/**
 * Displays a single platform preview result.
 * Shows rendered HTML, metadata, and any validation warnings.
 *
 * Provides two complementary personal-use workflows:
 * 1. Copy / Export — copy platform-specific content for manual publishing.
 * 2. Handoff — open official publish page with optional copy-before-open.
 */
export function PreviewCard({ preview, projectId, onDraftSaved }: PreviewCardProps) {
  const platformInfo = PLATFORM_OPTIONS.find((p) => p.id === preview.platform);
  const publishLink = getPublishHandoffLink(preview.platform);

  // ── Copy / Export state (from main, PR #20) ──
  const [copyStatus, setCopyStatus] = useState("");
  const [copyError, setCopyError] = useState("");
  const [draftStatus, setDraftStatus] = useState("");
  const [draftError, setDraftError] = useState("");
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  // ── Handoff state (PR #21) ──
  const [handoffChecklist, setHandoffChecklist] = useState<PublishHandoffChecklist>(
    INITIAL_PUBLISH_HANDOFF_CHECKLIST,
  );
  const [handoffStatus, setHandoffStatus] = useState<"handoff_ready" | "handoff_opened">(
    "handoff_ready",
  );
  const [handoffMessage, setHandoffMessage] = useState("");
  const [handoffError, setHandoffError] = useState("");

  // ── Copy / Export data (from main, PR #20) ──
  const hashtags = useMemo(() => {
    const rawTags = preview.metadata.hashtags ?? preview.metadata.tags;
    return Array.isArray(rawTags)
      ? rawTags.map((tag) => String(tag)).filter((tag) => tag.trim().length > 0)
      : [];
  }, [preview.metadata]);

  const cta =
    typeof preview.metadata.call_to_action === "string"
      ? preview.metadata.call_to_action
      : "";
  const copyExportText = [
    preview.title,
    "",
    preview.content,
    "",
    hashtags.map((tag) => `#${tag}`).join(" "),
    cta,
  ]
    .filter((part) => part.trim().length > 0)
    .join("\n");

  // ── Handoff data (PR #21) ──
  const previewTags = useMemo(() => getPreviewTags(preview.metadata), [preview.metadata]);
  const handoffCopyText = useMemo(
    () =>
      buildManualPublishText({
        title: preview.title,
        content: preview.content,
        metadata: preview.metadata,
      }),
    [preview.content, preview.metadata, preview.title],
  );

  // ── Handoff actions (PR #21) ──
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
      await navigator.clipboard.writeText(handoffCopyText);
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

  // ── Copy / Export actions (from main, PR #20) ──
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

  async function saveAsDraft(): Promise<void> {
    if (!projectId) return;

    setIsSavingDraft(true);
    setDraftStatus("");
    setDraftError("");
    try {
      const response = await api.createPublishDraft(projectId, {
        platform: preview.platform,
        title: preview.title,
        body: preview.content,
        hashtags,
        summary: typeof preview.metadata.summary === "string" ? preview.metadata.summary : "",
        cta,
        notes: preview.warnings.join("; "),
      });
      setDraftStatus("已保存到 OmniFlow-AI 系统内草稿箱");
      onDraftSaved?.(response.data);
    } catch (error) {
      setDraftError(getErrorMessage(error, "保存草稿失败，请稍后重试"));
    } finally {
      setIsSavingDraft(false);
    }
  }

  // ── Handoff checklist (PR #21) ──
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

      {/* Copy / Export actions — from main (PR #20) */}
      <div className="border-b border-slate-200 bg-white px-5 py-3 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void copyToClipboard("内容", copyExportText)}
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
          <button
            type="button"
            onClick={() => void saveAsDraft()}
            disabled={isSavingDraft || !projectId}
            className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-medium text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-300 dark:hover:bg-sky-950"
          >
            {isSavingDraft ? "保存中…" : "保存为草稿"}
          </button>
        </div>
        {(copyStatus || copyError || draftStatus || draftError) && (
          <p
            className={`mt-2 text-xs ${
              copyError || draftError
                ? "text-red-600 dark:text-red-400"
                : "text-green-700 dark:text-green-300"
            }`}
          >
            {copyError || draftError || copyStatus || draftStatus}
          </p>
        )}
      </div>

      {/* Publish handoff actions — PR #21 */}
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4 dark:border-slate-800 dark:bg-slate-900/70">
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                人工发布 — 打开官方页，手动提交
              </p>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                将打开平台官方发布页，你仍需要手动粘贴、检查并确认发布。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300">
                {HANDOFF_STATUS_LABELS[handoffStatus] ?? handoffStatus}
              </span>
              <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
                {publishLink ? HANDOFF_STATUS_LABELS[publishLink.status] ?? publishLink.status : "未知"}
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
              onClick={() => void copyBeforeOpen()}
              disabled={!publishLink}
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-slate-300"
            >
              复制并打开发布页
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
