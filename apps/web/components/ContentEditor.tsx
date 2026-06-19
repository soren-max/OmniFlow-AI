"use client";

interface ContentEditorProps {
  title: string;
  sourceText: string;
  onTitleChange: (value: string) => void;
  onSourceTextChange: (value: string) => void;
}

/**
 * Content input form — title + source text.
 */
export function ContentEditor({
  title,
  sourceText,
  onTitleChange,
  onSourceTextChange,
}: ContentEditorProps) {
  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="project-title"
          className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          内容标题 <span className="text-red-500">*</span>
        </label>
        <input
          id="project-title"
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="输入文章标题或内容主题"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm placeholder-slate-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:ring-sky-950"
        />
      </div>

      <div>
        <label
          htmlFor="project-source"
          className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          原始内容 <span className="text-red-500">*</span>
        </label>
        <textarea
          id="project-source"
          rows={10}
          value={sourceText}
          onChange={(e) => onSourceTextChange(e.target.value)}
          placeholder="粘贴或输入原始文章内容、博客、笔记…"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm placeholder-slate-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:ring-sky-950"
        />
        <p className="mt-1 text-xs text-gray-400">{sourceText.length} 字符</p>
      </div>
    </div>
  );
}
