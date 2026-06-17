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
              className={`rounded-xl border-2 p-4 text-left transition-all ${
                isActive
                  ? "border-blue-500 bg-blue-50 shadow-sm dark:border-blue-400 dark:bg-blue-900/20"
                  : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-600 dark:bg-gray-800"
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
                      ? "text-blue-700 dark:text-blue-300"
                      : "text-gray-800 dark:text-gray-200"
                  }`}
                >
                  {opt.label}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{opt.description}</p>
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
