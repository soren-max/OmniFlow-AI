"use client";

import { PLATFORM_OPTIONS, type Platform } from "@/types";

interface PlatformSelectorProps {
  selected: Platform[];
  onChange: (platforms: Platform[]) => void;
}

/**
 * Multi-select platform picker.
 * Displays all target platforms as clickable cards.
 */
export function PlatformSelector({ selected, onChange }: PlatformSelectorProps) {
  function toggle(platform: Platform) {
    if (selected.includes(platform)) {
      onChange(selected.filter((p) => p !== platform));
    } else {
      onChange([...selected, platform]);
    }
  }

  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
        目标平台 <span className="text-red-500">*</span>
      </label>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {PLATFORM_OPTIONS.map((opt) => {
          const isActive = selected.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => toggle(opt.id)}
              className={`rounded-xl border p-4 text-left shadow-sm transition-all ${
                isActive
                  ? "border-sky-300 bg-sky-50 ring-2 ring-sky-100 dark:border-sky-700 dark:bg-sky-950/30 dark:ring-sky-950"
                  : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: opt.color }}
                />
                <span
                  className={`text-sm font-semibold ${
                    isActive
                      ? "text-sky-700 dark:text-sky-300"
                      : "text-slate-800 dark:text-slate-200"
                  }`}
                >
                  {opt.label}
                </span>
              </div>
              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                {opt.description}
              </p>
            </button>
          );
        })}
      </div>
      {selected.length === 0 && (
        <p className="mt-1 text-xs text-amber-600">请选择至少一个目标平台</p>
      )}
    </div>
  );
}
