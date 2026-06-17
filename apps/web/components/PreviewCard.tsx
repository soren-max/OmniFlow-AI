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
    <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700">
      {/* Platform header */}
      <div
        className="flex items-center justify-between px-5 py-3 text-white"
        style={{ backgroundColor: platformInfo?.color ?? "#6366f1" }}
      >
        <span className="text-sm font-semibold">{preview.platform_display_name}</span>
        <span className="text-xs opacity-80">
          {preview.word_count} 字 · 约{preview.estimated_read_time_min}分钟
        </span>
      </div>

      {/* Warnings */}
      {preview.warnings.length > 0 && (
        <div className="bg-amber-50 px-5 py-2 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
          {preview.warnings.map((w, i) => (
            <p key={i}>⚠ {w}</p>
          ))}
        </div>
      )}

      {/* Rendered preview */}
      <div className="max-h-[500px] overflow-y-auto p-1">
        <div
          className="preview-content [&_img]:max-w-full [&_table]:w-full"
          dangerouslySetInnerHTML={{ __html: preview.rendered_html }}
        />
      </div>
    </div>
  );
}
