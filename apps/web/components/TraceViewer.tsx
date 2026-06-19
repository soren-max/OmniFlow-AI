"use client";

import type { AgentRun, AgentRunStatus, AgentStep } from "@/types";

interface TraceViewerProps {
  run: AgentRun | null;
  steps: AgentStep[];
  isLoading: boolean;
  errorMessage: string;
}

function statusClass(status: AgentRunStatus | string): string {
  if (status === "completed") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300";
  }
  if (status === "failed") {
    return "border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300";
  }
  return "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-300";
}

function formatDate(value?: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function formatLatency(value?: number | null): string {
  return value === undefined || value === null ? "-" : `${value} ms`;
}

export function TraceViewer({ run, steps, isLoading, errorMessage }: TraceViewerProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-sky-100 bg-sky-50 p-4 text-sm text-sky-700 dark:border-sky-900/40 dark:bg-sky-950/30 dark:text-sky-300">
        正在加载 Agent Trace...
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
        {errorMessage}
      </div>
    );
  }

  if (!run) {
    return null;
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">run_id</p>
          <code className="mt-1 block break-all font-mono text-slate-700 dark:text-slate-200">
            {run.run_id}
          </code>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">workflow_name</p>
          <p className="mt-1 font-medium text-slate-800 dark:text-slate-100">
            {run.workflow_name}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">status</p>
          <span
            className={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${statusClass(
              run.status,
            )}`}
          >
            {run.status}
          </span>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">started_at</p>
          <p className="mt-1 text-slate-700 dark:text-slate-200">{formatDate(run.started_at)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">finished_at</p>
          <p className="mt-1 text-slate-700 dark:text-slate-200">{formatDate(run.finished_at)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">total_latency_ms</p>
          <p className="mt-1 font-mono text-slate-700 dark:text-slate-200">
            {formatLatency(run.total_latency_ms)}
          </p>
        </div>
      </div>

      {run.error_message && (
        <div className="rounded-xl border border-red-100 bg-red-50 p-3 text-xs text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
          {run.error_message}
        </div>
      )}

      <div className="space-y-3">
        {steps.length > 0 ? (
          steps.map((step, index) => (
            <div
              key={step.step_id}
              className="relative rounded-xl border border-slate-200 bg-white p-4 text-xs dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-950 text-xs font-semibold text-white dark:bg-sky-500">
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-slate-100">
                      {step.node_name}
                    </p>
                    <p className="mt-0.5 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                      {formatLatency(step.latency_ms)}
                    </p>
                  </div>
                </div>
                <span
                  className={`inline-flex w-fit rounded-full border px-2 py-0.5 font-medium ${statusClass(
                    step.status,
                  )}`}
                >
                  {step.status}
                </span>
              </div>
              {step.error_message && (
                <p className="mt-3 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
                  {step.error_message}
                </p>
              )}
            </div>
          ))
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
            No steps recorded for this run.
          </div>
        )}
      </div>
    </div>
  );
}
