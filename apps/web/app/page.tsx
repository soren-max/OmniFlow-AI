"use client";

import { useState, useCallback } from "react";
import { ContentEditor } from "@/components/ContentEditor";
import { PlatformSelector } from "@/components/PlatformSelector";
import { PreviewCard } from "@/components/PreviewCard";
import { api, ApiError } from "@/lib/api";
import type {
  Platform,
  ProjectPreviewItem,
  ProjectResponse,
  GeneratePreviewResponse,
  PlatformPublishResultItem,
  EvaluationReportResponse,
  ReviewStatus,
} from "@/types";

type PageStep = "input" | "loading" | "result" | "error";

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

  const canSubmit =
    title.trim().length > 0 && sourceText.trim().length > 0 && selectedPlatforms.length > 0;

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;

    setStep("loading");
    setErrorMessage("");

    try {
      // Step 1: Create project
      const projectResp = await api.post<ProjectResponse>("/api/projects", {
        title: title.trim(),
        source_text: sourceText.trim(),
      });
      const project = projectResp.data;

      // Step 2: Generate previews
      const previewResp = await api.post<GeneratePreviewResponse>(
        `/api/projects/${project.id}/preview`,
        { platforms: selectedPlatforms },
      );

      setPreviews(previewResp.data.previews);
      setProjectId(project.id);
      setProjectTitle(project.title);
      setPublishPlatforms(selectedPlatforms);
      setPublishResults([]);
      setPublishError("");
      setReviewStatus("pending");
      setReviewError("");
      setEvaluationReport(null);
      setEvaluationError("");
      setStep("result");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(
          err.status === 0
            ? "无法连接到后端服务，请确认后端已启动"
            : `请求失败 (${err.status}): ${err.message}`,
        );
      } else {
        setErrorMessage("发生未知错误，请稍后重试");
      }
      setStep("error");
    }
  }, [title, sourceText, selectedPlatforms, canSubmit]);

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
  }, []);

  const handleEvaluation = useCallback(async () => {
    if (!projectId) return;

    setIsEvaluating(true);
    setEvaluationError("");

    try {
      const response = await api.createEvaluation(projectId);
      setEvaluationReport(response.data);
    } catch (err) {
      if (err instanceof ApiError) {
        setEvaluationError(`评测失败 (${err.status}): ${err.message}`);
      } else {
        setEvaluationError("评测失败，请稍后重试");
      }
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
      if (err instanceof ApiError) {
        setReviewError(`审核失败 (${err.status}): ${err.message}`);
      } else {
        setReviewError("审核失败，请稍后重试");
      }
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
      if (err instanceof ApiError) {
        setReviewError(`审核失败 (${err.status}): ${err.message}`);
      } else {
        setReviewError("审核失败，请稍后重试");
      }
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
      if (err instanceof ApiError) {
        setPublishError(`发布失败 (${err.status}): ${err.message}`);
      } else {
        setPublishError("发布失败，请稍后重试");
      }
    } finally {
      setIsPublishing(false);
    }
  }, [projectId, publishPlatforms, reviewStatus]);

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">ContentOps Agent</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Enterprise AI Agent platform for multi-platform content operations.
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

      <div className="mx-auto max-w-5xl px-6 py-8">
        {/* ── Input Step ── */}
        {step === "input" && (
          <div className="space-y-6">
            <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
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

            <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <h2 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-200">
                目标平台
              </h2>
              <PlatformSelector selected={selectedPlatforms} onChange={setSelectedPlatforms} />
            </div>

            <div className="flex justify-center">
              <button
                onClick={handleSubmit}
                disabled={!canSubmit}
                className={`rounded-xl px-10 py-3 text-sm font-semibold text-white shadow-sm transition ${
                  canSubmit
                    ? "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
                    : "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                }`}
              >
                生成多平台预览
              </button>
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
