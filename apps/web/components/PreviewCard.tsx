"use client";

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
