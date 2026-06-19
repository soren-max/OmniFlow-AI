"use client";

import { useState, useCallback } from "react";
import { ContentEditor } from "@/components/ContentEditor";
import { PlatformSelector } from "@/components/PlatformSelector";
import { PreviewCard } from "@/components/PreviewCard";
import { TraceViewer } from "@/components/TraceViewer";
import { api, getErrorMessage } from "@/lib/api";
import type {
  AgentRun,
  AgentStep,
  Platform,
  ProjectPreviewItem,
  ProjectResponse,
  GeneratePreviewResponse,
  PlatformPublishResultItem,
  EvaluationReportResponse,
  ReviewStatus,
} from "@/types";

type PageStep = "input" | "loading" | "result" | "error";

const CAPABILITY_BADGES = [
  "Multi-platform preview",
  "LangGraph workflow",
  "Trace",
  "Human Review",
  "Mock Publish",
  "Evaluation",
];

const WORKFLOW_STEPS = [
  "Input",
  "Platform Strategy",
  "Preview Generation",
  "Review",
  "Mock Publish",
  "Evaluation",
];

export default function Home() {
  const [title, setTitle] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([]);
  const [step, setStep] = useState<PageStep>("input");
  const [previews, setPreviews] = useState<ProjectPreviewItem[]>([]);
  const [projectId, setProjectId] = useState("");
  const [projectTitle, setProjectTitle] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [publishPlatforms, setPublishPlatforms] = useState<Platform[]>([]);
  const [publishResults, setPublishResults] = useState<PlatformPublishResultItem[]>([]);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishError, setPublishError] = useState("");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("pending");
  const [isReviewing, setIsReviewing] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [evaluationReport, setEvaluationReport] = useState<EvaluationReportResponse | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationError, setEvaluationError] = useState("");
  const [runId, setRunId] = useState("");
  const [traceRun, setTraceRun] = useState<AgentRun | null>(null);
  const [traceSteps, setTraceSteps] = useState<AgentStep[]>([]);
  const [isTraceVisible, setIsTraceVisible] = useState(false);
  const [isTraceLoading, setIsTraceLoading] = useState(false);
  const [traceError, setTraceError] = useState("");

  const trimmedTitle = title.trim();
  const trimmedSourceText = sourceText.trim();
  const titleValidationMessage =
    trimmedTitle.length > 0 && trimmedTitle.length < 2 ? "标题至少 2 个字符" : "";
  const sourceTextValidationMessage =
    trimmedSourceText.length > 0 && trimmedSourceText.length < 20 ? "正文至少 20 个字符" : "";
  const canSubmit =
    trimmedTitle.length >= 2 && trimmedSourceText.length >= 20 && selectedPlatforms.length > 0;

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;

    setStep("loading");
    setErrorMessage("");

    try {
      // Step 1: Create project
      const projectResp = await api.post<ProjectResponse>("/api/projects", {
        title: trimmedTitle,
        source_text: trimmedSourceText,
      });
      const project = projectResp.data;

      // Step 2: Generate previews
      const previewResp = await api.post<GeneratePreviewResponse>(
        `/api/projects/${project.id}/preview`,
        { platforms: selectedPlatforms },
      );
      const agentPreviewResp = await api.generateAgentPreview(project.id, {
        platforms: selectedPlatforms,
      });

      setPreviews(previewResp.data.previews);
      setProjectId(project.id);
      setProjectTitle(project.title);
      setRunId(agentPreviewResp.data.run_id ?? "");
      setTraceRun(null);
      setTraceSteps([]);
      setIsTraceVisible(false);
      setIsTraceLoading(false);
      setTraceError("");
      setPublishPlatforms(selectedPlatforms);
      setPublishResults([]);
      setPublishError("");
      setReviewStatus("pending");
      setReviewError("");
      setEvaluationReport(null);
      setEvaluationError("");
      setStep("result");
    } catch (err) {
      setErrorMessage(getErrorMessage(err, "生成预览失败，请稍后重试"));
      setStep("error");
    }
  }, [trimmedTitle, trimmedSourceText, selectedPlatforms, canSubmit]);

  const handleReset = useCallback(() => {
    setStep("input");
    setPreviews([]);
    setProjectId("");
    setProjectTitle("");
    setErrorMessage("");
    setPublishPlatforms([]);
    setPublishResults([]);
    setPublishError("");
    setIsPublishing(false);
    setReviewStatus("pending");
    setReviewError("");
    setIsReviewing(false);
    setEvaluationReport(null);
    setEvaluationError("");
    setIsEvaluating(false);
    setRunId("");
    setTraceRun(null);
    setTraceSteps([]);
    setIsTraceVisible(false);
    setIsTraceLoading(false);
    setTraceError("");
  }, []);

  const handleViewTrace = useCallback(async () => {
    if (!runId) return;

    setIsTraceVisible(true);
    setIsTraceLoading(true);
    setTraceError("");

    try {
      const [runResp, stepsResp] = await Promise.all([
        api.getAgentRun(runId),
        api.listAgentSteps(runId),
      ]);
      setTraceRun(runResp.data);
      setTraceSteps(stepsResp.data);
    } catch (err) {
      setTraceError(getErrorMessage(err, "Trace 加载失败，请稍后重试"));
    } finally {
      setIsTraceLoading(false);
    }
  }, [runId]);

  const handleEvaluation = useCallback(async () => {
    if (!projectId) return;

    setIsEvaluating(true);
    setEvaluationError("");

    try {
      const response = await api.createEvaluation(projectId);
      setEvaluationReport(response.data);
    } catch (err) {
      setEvaluationError(getErrorMessage(err, "评测失败，请稍后重试"));
    } finally {
      setIsEvaluating(false);
    }
  }, [projectId]);

  const handleApprove = useCallback(async () => {
    if (!projectId) return;

    setIsReviewing(true);
    setReviewError("");
    setPublishError("");

    try {
      const response = await api.approveProject(projectId);
      setReviewStatus(response.data.status as ReviewStatus);
    } catch (err) {
      setReviewError(getErrorMessage(err, "审核失败，请稍后重试"));
    } finally {
      setIsReviewing(false);
    }
  }, [projectId]);

  const handleReject = useCallback(async () => {
    if (!projectId) return;

    setIsReviewing(true);
    setReviewError("");
    setPublishError("");

    try {
      const response = await api.rejectProject(projectId);
      setReviewStatus(response.data.status as ReviewStatus);
      setPublishResults([]);
    } catch (err) {
      setReviewError(getErrorMessage(err, "审核失败，请稍后重试"));
    } finally {
      setIsReviewing(false);
    }
  }, [projectId]);

  const handleMockPublish = useCallback(async () => {
    if (!projectId || publishPlatforms.length === 0) return;
    if (reviewStatus !== "approved") {
      setPublishError("Mock Publish 前需要先通过人工审核");
      return;
    }

    setIsPublishing(true);
    setPublishError("");

    try {
      const publishResp = await api.publishProject(projectId, {
        target_platforms: publishPlatforms,
        mode: "mock",
      });
      setPublishResults(publishResp.data.results);
    } catch (err) {
      setPublishError(getErrorMessage(err, "发布失败，请稍后重试"));
    } finally {
      setIsPublishing(false);
    }
  }, [projectId, publishPlatforms, reviewStatus]);

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#eef6ff_0%,#f8fafc_35%,#ffffff_100%)] dark:bg-[linear-gradient(180deg,#07111f_0%,#0f172a_42%,#111827_100%)]">
      {/* Header */}
      <header className="border-b border-white/70 bg-white/80 backdrop-blur dark:border-gray-700 dark:bg-gray-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-bold text-gray-900 dark:text-white">OmniFlow-AI</h1>
              <span className="rounded-full border border-sky-200 bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/40 dark:text-sky-300">
                v0.1.0-alpha
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              AI Content Operations Agent for traceable, reviewable demo workflows.
            </p>
          </div>
          {step !== "input" && (
            <button
              onClick={handleReset}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              ← 新建项目
            </button>
          )}
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-8">
        <section className="mb-8 rounded-2xl border border-white/70 bg-white/85 p-6 shadow-sm backdrop-blur dark:border-gray-800 dark:bg-gray-950/70">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-700 dark:text-sky-300">
                AI Content Operations Agent
              </p>
              <h2 className="mt-3 max-w-3xl text-3xl font-bold tracking-tight text-gray-950 dark:text-white">
                Multi-platform preview with workflow trace, review gate, mock publish, and
                evaluation.
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-gray-600 dark:text-gray-300">
                A demo dashboard for showing adapter-driven content operations without real LLM
                calls or real platform publishing.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {CAPABILITY_BADGES.map((badge) => (
                  <span
                    key={badge}
                    className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/80">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
                Workflow strip
              </p>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {WORKFLOW_STEPS.map((item, index) => (
                  <div key={item} className="flex items-center gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white dark:bg-gray-100 dark:text-gray-950">
                      {index + 1}
                    </span>
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-200">
                      {item}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Input Step ── */}
        {step === "input" && (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-950">
              <h2 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-200">
                内容输入
              </h2>
              <ContentEditor
                title={title}
                sourceText={sourceText}
                onTitleChange={setTitle}
                onSourceTextChange={setSourceText}
              />
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-950">
              <h2 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-200">
                目标平台
              </h2>
              <PlatformSelector selected={selectedPlatforms} onChange={setSelectedPlatforms} />

              <div className="mt-6 rounded-xl border border-sky-200 bg-sky-50 p-4 text-xs leading-5 text-sky-800 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-200">
                <p className="font-semibold">Demo guardrails</p>
                <p className="mt-1">No real LLM calls. No real platform publishing.</p>
                <p>Mock Publish requires Human Review approval.</p>
              </div>

              <div className="mt-6">
                <button
                  onClick={handleSubmit}
                  disabled={!canSubmit}
                  className={`w-full rounded-xl px-10 py-3 text-sm font-semibold text-white shadow-sm transition ${
                    canSubmit
                      ? "bg-gray-950 hover:bg-gray-800 active:bg-black dark:bg-sky-500 dark:hover:bg-sky-400"
                      : "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                  }`}
                >
                  生成多平台预览
                </button>
                {(titleValidationMessage || sourceTextValidationMessage) && (
                  <div className="mt-3 space-y-1 text-xs text-amber-700 dark:text-amber-300">
                    {titleValidationMessage && <p>{titleValidationMessage}</p>}
                    {sourceTextValidationMessage && <p>{sourceTextValidationMessage}</p>}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Loading Step ── */}
        {step === "loading" && (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="mb-6 h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
            <p className="text-sm text-gray-500 dark:text-gray-400">正在生成平台预览…</p>
            <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
              正在为 {selectedPlatforms.length} 个平台适配内容
            </p>
          </div>
        )}

        {/* ── Error Step ── */}
        {step === "error" && (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="mb-4 text-4xl">⚠️</div>
            <p className="mb-2 text-sm font-semibold text-red-600 dark:text-red-400">
              生成预览失败
            </p>
            <p className="mb-6 max-w-md text-center text-xs text-gray-500 dark:text-gray-400">
              {errorMessage}
            </p>
            <button
              onClick={handleReset}
              className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              返回重试
            </button>
          </div>
        )}

        {/* ── Result Step ── */}
        {step === "result" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-200">预览结果</h2>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {projectTitle} — 已为 {previews.length} 个平台生成预览
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">
                    Agent Trace
                  </h3>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Basic run and step trace from the deterministic Agent Preview workflow
                  </p>
                </div>
                <button
                  onClick={handleViewTrace}
                  disabled={!runId || isTraceLoading}
                  className={`rounded-lg px-5 py-2 text-sm font-semibold text-white transition ${
                    !runId || isTraceLoading
                      ? "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                      : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
                  }`}
                >
                  {isTraceLoading ? "Loading Trace..." : "View Trace"}
                </button>
              </div>

              <div className="mt-4">
                <p className="text-xs text-gray-500 dark:text-gray-400">run_id</p>
                {runId ? (
                  <code className="mt-1 block break-all rounded bg-gray-50 px-3 py-2 text-xs text-gray-700 dark:bg-gray-900 dark:text-gray-200">
                    {runId}
                  </code>
                ) : (
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    当前 preview 未返回可查询的 Agent Trace。
                  </p>
                )}
              </div>

              {isTraceVisible && (
                <div className="mt-5">
                  <TraceViewer
                    run={traceRun}
                    steps={traceSteps}
                    isLoading={isTraceLoading}
                    errorMessage={traceError}
                  />
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {previews.map((preview) => (
                <PreviewCard key={preview.platform} preview={preview} />
              ))}
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">
                    Evaluation Report
                  </h3>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Rule-based quality scores for generated previews
                  </p>
                </div>
                <button
                  onClick={handleEvaluation}
                  disabled={isEvaluating || previews.length === 0}
                  className={`rounded-lg px-5 py-2 text-sm font-semibold text-white transition ${
                    isEvaluating || previews.length === 0
                      ? "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                      : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
                  }`}
                >
                  {isEvaluating ? "正在评测…" : "Run Evaluation"}
                </button>
              </div>

              {evaluationError && (
                <p className="mt-3 text-xs text-red-600 dark:text-red-400">{evaluationError}</p>
              )}

              {evaluationReport && (
                <div className="mt-5 space-y-5">
                  <div className="flex items-end gap-3">
                    <span className="text-4xl font-bold text-gray-900 dark:text-white">
                      {evaluationReport.average_score}
                    </span>
                    <span className="pb-1 text-sm text-gray-500 dark:text-gray-400">
                      average_score
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                    {evaluationReport.platform_scores.map((score) => (
                      <div
                        key={score.platform}
                        className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900"
                      >
                        <div className="mb-3 flex items-center justify-between gap-3">
                          <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                            {score.platform_display_name}
                          </span>
                          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                            {score.overall_score}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-300">
                          <span>format {score.format_score}</span>
                          <span>style {score.style_score}</span>
                          <span>consistency {score.consistency_score}</span>
                          <span>compliance {score.compliance_score}</span>
                          <span>completeness {score.completeness_score}</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {(evaluationReport.issues.length > 0 ||
                    evaluationReport.suggestions.length > 0) && (
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                      <div>
                        <h4 className="mb-2 text-sm font-semibold text-gray-800 dark:text-gray-100">
                          Issues
                        </h4>
                        <ul className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
                          {evaluationReport.issues.length > 0 ? (
                            evaluationReport.issues.map((issue) => (
                              <li key={issue}>- {issue}</li>
                            ))
                          ) : (
                            <li>No blocking issues found.</li>
                          )}
                        </ul>
                      </div>
                      <div>
                        <h4 className="mb-2 text-sm font-semibold text-gray-800 dark:text-gray-100">
                          Suggestions
                        </h4>
                        <ul className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
                          {evaluationReport.suggestions.length > 0 ? (
                            evaluationReport.suggestions.map((suggestion) => (
                              <li key={suggestion}>- {suggestion}</li>
                            ))
                          ) : (
                            <li>No suggestions for the current previews.</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                      Human Review
                    </h3>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      当前状态：{reviewStatus}
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleReject}
                      disabled={isReviewing || reviewStatus === "rejected"}
                      className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
                        isReviewing || reviewStatus === "rejected"
                          ? "cursor-not-allowed border-gray-200 text-gray-400 dark:border-gray-700"
                          : "border-red-200 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950/30"
                      }`}
                    >
                      Reject
                    </button>
                    <button
                      onClick={handleApprove}
                      disabled={isReviewing || reviewStatus === "approved"}
                      className={`rounded-lg px-4 py-2 text-sm font-medium text-white transition ${
                        isReviewing || reviewStatus === "approved"
                          ? "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                          : "bg-green-600 hover:bg-green-700 active:bg-green-800"
                      }`}
                    >
                      Approve
                    </button>
                  </div>
                </div>

                {reviewError && (
                  <p className="mt-3 text-xs text-red-600 dark:text-red-400">{reviewError}</p>
                )}
              </div>

              <h3 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-200">
                Mock Publish
              </h3>
              <PlatformSelector selected={publishPlatforms} onChange={setPublishPlatforms} />
              <div className="mt-5 flex justify-center">
                <button
                  onClick={handleMockPublish}
                  disabled={
                    isPublishing || publishPlatforms.length === 0 || reviewStatus !== "approved"
                  }
                  className={`rounded-xl px-8 py-2.5 text-sm font-semibold text-white shadow-sm transition ${
                    isPublishing || publishPlatforms.length === 0 || reviewStatus !== "approved"
                      ? "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                      : "bg-gray-900 hover:bg-gray-800 active:bg-black dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white"
                  }`}
                >
                  {isPublishing ? "正在 Mock Publish…" : "Mock Publish"}
                </button>
              </div>

              {publishError && (
                <p className="mt-3 text-center text-xs text-red-600 dark:text-red-400">
                  {publishError}
                </p>
              )}

              {publishResults.length > 0 && (
                <div className="mt-5 space-y-3">
                  {publishResults.map((result) => (
                    <div
                      key={result.platform}
                      className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm dark:border-gray-700 dark:bg-gray-900"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold text-gray-800 dark:text-gray-100">
                          {result.platform_display_name}
                        </span>
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-300">
                          {result.status}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        {result.message}
                      </p>
                      {result.mock_url && (
                        <code className="mt-2 block break-all rounded bg-white px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                          {result.mock_url}
                        </code>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-center gap-4">
              <button
                onClick={handleReset}
                className="rounded-lg border border-gray-300 px-6 py-2 text-sm text-gray-600 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                ← 新建项目
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
