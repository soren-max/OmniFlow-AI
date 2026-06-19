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
    return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
  }
  if (status === "failed") {
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
  }
  return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300";
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
      <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300">
        正在加载 Agent Trace...
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
        {errorMessage}
      </div>
    );
  }

  if (!run) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <p className="text-gray-500 dark:text-gray-400">run_id</p>
          <code className="mt-1 block break-all rounded bg-gray-50 px-2 py-1 text-gray-700 dark:bg-gray-900 dark:text-gray-200">
            {run.run_id}
          </code>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">workflow_name</p>
          <p className="mt-1 font-medium text-gray-800 dark:text-gray-100">{run.workflow_name}</p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">status</p>
          <span
            className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusClass(
              run.status,
            )}`}
          >
            {run.status}
          </span>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">started_at</p>
          <p className="mt-1 text-gray-700 dark:text-gray-200">{formatDate(run.started_at)}</p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">finished_at</p>
          <p className="mt-1 text-gray-700 dark:text-gray-200">{formatDate(run.finished_at)}</p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">total_latency_ms</p>
          <p className="mt-1 text-gray-700 dark:text-gray-200">
            {formatLatency(run.total_latency_ms)}
          </p>
        </div>
      </div>

      {run.error_message && (
        <div className="rounded-lg border border-red-100 bg-red-50 p-3 text-xs text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
          {run.error_message}
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-[1.4fr_0.9fr_0.9fr] gap-3 bg-gray-50 px-4 py-2 text-xs font-semibold text-gray-500 dark:bg-gray-900 dark:text-gray-400">
          <span>node_name</span>
          <span>status</span>
          <span>latency_ms</span>
        </div>
        {steps.length > 0 ? (
          steps.map((step) => (
            <div
              key={step.step_id}
              className="border-t border-gray-200 px-4 py-3 text-xs dark:border-gray-700"
            >
              <div className="grid grid-cols-[1.4fr_0.9fr_0.9fr] items-center gap-3">
                <span className="font-medium text-gray-800 dark:text-gray-100">
                  {step.node_name}
                </span>
                <span
                  className={`inline-flex w-fit rounded-full px-2 py-0.5 font-medium ${statusClass(
                    step.status,
                  )}`}
                >
                  {step.status}
                </span>
                <span className="text-gray-600 dark:text-gray-300">
                  {formatLatency(step.latency_ms)}
                </span>
              </div>
              {step.error_message && (
                <p className="mt-2 rounded bg-red-50 px-2 py-1 text-red-700 dark:bg-red-950/30 dark:text-red-300">
                  {step.error_message}
                </p>
              )}
            </div>
          ))
        ) : (
          <div className="border-t border-gray-200 px-4 py-3 text-xs text-gray-500 dark:border-gray-700 dark:text-gray-400">
            No steps recorded for this run.
          </div>
        )}
      </div>
    </div>
  );
}
