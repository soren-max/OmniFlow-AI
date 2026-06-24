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
  PublishDraft,
  PublishDraftStatus,
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
  "Save Draft",
  "Manual Handoff",
  "Mock Publish",
  "Evaluation",
];

const DRAFT_STATUS_LABELS: Record<PublishDraftStatus, string> = {
  draft: "草稿",
  reviewed: "已复核",
  exported: "已导出",
  handoff_opened: "已打开发布页",
  archived: "已归档",
};

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
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState("");
  const [exportError, setExportError] = useState("");
  const [drafts, setDrafts] = useState<PublishDraft[]>([]);
  const [selectedDraftId, setSelectedDraftId] = useState("");
  const [draftTitle, setDraftTitle] = useState("");
  const [draftBody, setDraftBody] = useState("");
  const [draftHashtags, setDraftHashtags] = useState("");
  const [draftNotes, setDraftNotes] = useState("");
  const [draftMessage, setDraftMessage] = useState("");
  const [draftError, setDraftError] = useState("");
  const [isDraftBusy, setIsDraftBusy] = useState(false);

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
      setExportMessage("");
      setExportError("");
      setIsExporting(false);
      setDrafts([]);
      setSelectedDraftId("");
      setDraftMessage("");
      setDraftError("");
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
    setIsExporting(false);
    setExportMessage("");
    setExportError("");
    setDrafts([]);
    setSelectedDraftId("");
    setDraftTitle("");
    setDraftBody("");
    setDraftHashtags("");
    setDraftNotes("");
    setDraftMessage("");
    setDraftError("");
    setIsDraftBusy(false);
  }, []);

  const downloadFile = useCallback((filename: string, content: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }, []);

  const handleExportMarkdown = useCallback(async () => {
    if (!projectId) return;

    setIsExporting(true);
    setExportMessage("");
    setExportError("");

    try {
      const response = await api.getPublishPackageMarkdown(projectId);
      downloadFile(
        `omniflow-publish-package-${projectId}.md`,
        response.data,
        "text/markdown;charset=utf-8",
      );
      setExportMessage("Markdown 发布包已下载");
    } catch (err) {
      setExportError(getErrorMessage(err, "导出 Markdown 失败，请稍后重试"));
    } finally {
      setIsExporting(false);
    }
  }, [downloadFile, projectId]);

  const handleExportJson = useCallback(async () => {
    if (!projectId) return;

    setIsExporting(true);
    setExportMessage("");
    setExportError("");

    try {
      const response = await api.getPublishPackage(projectId);
      downloadFile(
        `omniflow-publish-package-${projectId}.json`,
        JSON.stringify(response.data, null, 2),
        "application/json;charset=utf-8",
      );
      setExportMessage("JSON 发布包已下载");
    } catch (err) {
      setExportError(getErrorMessage(err, "导出 JSON 失败，请稍后重试"));
    } finally {
      setIsExporting(false);
    }
  }, [downloadFile, projectId]);

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

  const selectedDraft = drafts.find((draft) => draft.draft_id === selectedDraftId) ?? null;

  const upsertDraft = useCallback((draft: PublishDraft) => {
    setDrafts((current) => {
      const existing = current.some((item) => item.draft_id === draft.draft_id);
      if (existing) {
        return current.map((item) => (item.draft_id === draft.draft_id ? draft : item));
      }
      return [draft, ...current];
    });
    setSelectedDraftId(draft.draft_id);
    setDraftTitle(draft.title);
    setDraftBody(draft.body);
    setDraftHashtags(draft.hashtags.join(", "));
    setDraftNotes(draft.notes);
    setDraftMessage("草稿已保存。");
    setDraftError("");
  }, []);

  const selectDraft = useCallback((draft: PublishDraft) => {
    setSelectedDraftId(draft.draft_id);
    setDraftTitle(draft.title);
    setDraftBody(draft.body);
    setDraftHashtags(draft.hashtags.join(", "));
    setDraftNotes(draft.notes);
    setDraftMessage("");
    setDraftError("");
  }, []);

  const refreshDrafts = useCallback(async () => {
    if (!projectId) return;
    setIsDraftBusy(true);
    setDraftError("");
    try {
      const response = await api.listPublishDrafts(projectId);
      setDrafts(response.data);
      if (!selectedDraftId && response.data.length > 0) {
        selectDraft(response.data[0]);
      }
      setDraftMessage("草稿列表已刷新。");
    } catch (error) {
      setDraftError(getErrorMessage(error, "加载草稿失败，请稍后重试"));
    } finally {
      setIsDraftBusy(false);
    }
  }, [projectId, selectDraft, selectedDraftId]);

  const saveDraftEdits = useCallback(async () => {
    if (!selectedDraft) return;
    setIsDraftBusy(true);
    setDraftMessage("");
    setDraftError("");
    try {
      const response = await api.updatePublishDraft(selectedDraft.draft_id, {
        title: draftTitle,
        body: draftBody,
        hashtags: draftHashtags
          .split(/[,，\s]+/)
          .map((tag) => tag.trim().replace(/^#/, ""))
          .filter(Boolean),
        notes: draftNotes,
      });
      upsertDraft(response.data);
      setDraftMessage("草稿已更新。");
    } catch (error) {
      setDraftError(getErrorMessage(error, "更新草稿失败，请稍后重试"));
    } finally {
      setIsDraftBusy(false);
    }
  }, [draftBody, draftHashtags, draftNotes, draftTitle, selectedDraft, upsertDraft]);

  const copyDraftContent = useCallback(async (draft: PublishDraft) => {
    setDraftMessage("");
    setDraftError("");
    if (!navigator.clipboard) {
      setDraftError("当前浏览器不支持 Clipboard API");
      return;
    }
    const text = [
      draft.title,
      "",
      draft.body,
      "",
      draft.hashtags.map((tag) => `#${tag}`).join(" "),
      draft.cta,
    ]
      .filter((part) => part.trim().length > 0)
      .join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setDraftMessage("草稿内容已复制。");
    } catch (error) {
      setDraftError(getErrorMessage(error, "复制草稿失败，请稍后重试"));
    }
  }, []);

  const exportDraft = useCallback(
    async (draft: PublishDraft, format: "json" | "markdown") => {
      setIsDraftBusy(true);
      setDraftMessage("");
      setDraftError("");
      try {
        const response = await api.exportPublishDraft(draft.draft_id, format);
        downloadFile(
          response.data.filename,
          response.data.content,
          format === "json" ? "application/json;charset=utf-8" : "text/markdown;charset=utf-8",
        );
        const refreshed = await api.listPublishDrafts(draft.project_id);
        setDrafts(refreshed.data);
        setDraftMessage(`${format === "json" ? "JSON" : "Markdown"} 草稿已导出。`);
      } catch (error) {
        setDraftError(getErrorMessage(error, "导出草稿失败，请稍后重试"));
      } finally {
        setIsDraftBusy(false);
      }
    },
    [downloadFile],
  );

  const openDraftHandoff = useCallback(async (draft: PublishDraft) => {
    setIsDraftBusy(true);
    setDraftMessage("");
    setDraftError("");
    try {
      const response = await api.openPublishDraftHandoff(draft.draft_id);
      upsertDraft(response.data.draft);
      window.open(response.data.official_publish_url, "_blank", "noopener,noreferrer");
      setDraftMessage(response.data.message);
    } catch (error) {
      setDraftError(getErrorMessage(error, "打开官方发布页失败，请稍后重试"));
    } finally {
      setIsDraftBusy(false);
    }
  }, [upsertDraft]);

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


              <div className="mt-6 space-y-3">
                {/* DeepSeek status indicator */}
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs leading-5 text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200">
                  <p className="font-semibold">⚡ DeepSeek 已启用</p>
                  <p className="mt-1">
                    LLM_PROVIDER=deepseek，使用 DeepSeek 生成平台内容。如改用 Mock 模式，请在 .env 中设置 LLM_PROVIDER=mock。
                  </p>
                </div>

                {/* Publishing mode clarification */}
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
                  <div className="space-y-2">
                    <p className="font-semibold">📋 发布流程说明</p>
                    <div className="flex items-start gap-2">
                      <span className="mt-0.5 shrink-0 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">模拟</span>
                      <span><strong>Mock Publish</strong> — 模拟发布，记录模拟结果，需先通过人工审核。</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="mt-0.5 shrink-0 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">人工</span>
                      <span><strong>打开发布页</strong> — 打开平台官方发布页，仍需手动粘贴、检查并确认提交。不使用 Cookie / Playwright / Selenium。</span>
                    </div>
                  </div>
                </div>

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
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">
                    Publish Package Export
                  </h3>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Generate, review, evaluate, export, copy, then manually publish.
                  </p>
                  {reviewStatus !== "approved" && (
                    <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                      当前状态为 {reviewStatus}，导出包会标记为 draft。
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => void handleExportMarkdown()}
                    disabled={isExporting || previews.length === 0}
                    className={`rounded-lg px-5 py-2 text-sm font-semibold text-white transition ${
                      isExporting || previews.length === 0
                        ? "cursor-not-allowed bg-gray-300 dark:bg-gray-600"
                        : "bg-slate-900 hover:bg-slate-800 dark:bg-sky-500 dark:hover:bg-sky-400"
                    }`}
                  >
                    导出 Markdown
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleExportJson()}
                    disabled={isExporting || previews.length === 0}
                    className={`rounded-lg border px-5 py-2 text-sm font-semibold transition ${
                      isExporting || previews.length === 0
                        ? "cursor-not-allowed border-gray-200 text-gray-400 dark:border-gray-700"
                        : "border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
                    }`}
                  >
                    导出 JSON
                  </button>
                </div>
              </div>
              {(exportMessage || exportError) && (
                <p
                  className={`mt-3 text-xs ${
                    exportError
                      ? "text-red-600 dark:text-red-400"
                      : "text-green-700 dark:text-green-300"
                  }`}
                >
                  {exportError || exportMessage}
                </p>
              )}
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
                <PreviewCard
                  key={preview.platform}
                  preview={preview}
                  projectId={projectId}
                  onDraftSaved={upsertDraft}
                />
              ))}
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">
                    发布草稿箱
                  </h3>
                  <p className="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">
                    这是 OmniFlow-AI 系统内草稿箱，不是平台官方草稿箱。发布仍需要你进入平台官方发布页手动确认提交。
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void refreshDrafts()}
                  disabled={isDraftBusy || !projectId}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-900"
                >
                  刷新草稿
                </button>
              </div>

              {drafts.length === 0 ? (
                <div className="mt-5 rounded-lg border border-dashed border-gray-300 p-4 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
                  还没有发布草稿。可以在任一平台 PreviewCard 中点击“保存为草稿”。
                </div>
              ) : (
                <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                  <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
                    <div className="grid grid-cols-[0.7fr_1fr_0.7fr_0.9fr] gap-2 border-b border-gray-200 bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
                      <span>平台</span>
                      <span>标题</span>
                      <span>状态</span>
                      <span>更新时间</span>
                    </div>
                    <div className="divide-y divide-gray-200 dark:divide-gray-700">
                      {drafts.map((draft) => (
                        <button
                          key={draft.draft_id}
                          type="button"
                          onClick={() => selectDraft(draft)}
                          className={`grid w-full grid-cols-[0.7fr_1fr_0.7fr_0.9fr] gap-2 px-3 py-3 text-left text-xs transition ${
                            selectedDraftId === draft.draft_id
                              ? "bg-sky-50 text-sky-900 dark:bg-sky-950/40 dark:text-sky-100"
                              : "text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-gray-900"
                          }`}
                        >
                          <span>{draft.platform}</span>
                          <span className="truncate">{draft.title}</span>
                          <span>{DRAFT_STATUS_LABELS[draft.status]}</span>
                          <span>{new Date(draft.updated_at).toLocaleString()}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {selectedDraft && (
                    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                      <div className="mb-4 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => void copyDraftContent(selectedDraft)}
                          className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-900"
                        >
                          复制
                        </button>
                        <button
                          type="button"
                          onClick={() => void exportDraft(selectedDraft, "markdown")}
                          disabled={isDraftBusy}
                          className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-900"
                        >
                          导出 Markdown
                        </button>
                        <button
                          type="button"
                          onClick={() => void exportDraft(selectedDraft, "json")}
                          disabled={isDraftBusy}
                          className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-900"
                        >
                          导出 JSON
                        </button>
                        <button
                          type="button"
                          onClick={() => void openDraftHandoff(selectedDraft)}
                          disabled={isDraftBusy}
                          className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-950 dark:hover:bg-white"
                        >
                          打开发布页
                        </button>
                      </div>

                      <div className="space-y-3">
                        <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300">
                          标题
                          <input
                            value={draftTitle}
                            onChange={(event) => setDraftTitle(event.target.value)}
                            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-normal text-gray-900 outline-none transition focus:border-sky-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                          />
                        </label>
                        <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300">
                          正文
                          <textarea
                            value={draftBody}
                            onChange={(event) => setDraftBody(event.target.value)}
                            rows={7}
                            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-normal leading-6 text-gray-900 outline-none transition focus:border-sky-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                          />
                        </label>
                        <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300">
                          标签
                          <input
                            value={draftHashtags}
                            onChange={(event) => setDraftHashtags(event.target.value)}
                            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-normal text-gray-900 outline-none transition focus:border-sky-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                          />
                        </label>
                        <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300">
                          备注
                          <textarea
                            value={draftNotes}
                            onChange={(event) => setDraftNotes(event.target.value)}
                            rows={3}
                            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-normal leading-6 text-gray-900 outline-none transition focus:border-sky-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                          />
                        </label>
                      </div>

                      <button
                        type="button"
                        onClick={() => void saveDraftEdits()}
                        disabled={isDraftBusy || !draftTitle.trim() || !draftBody.trim()}
                        className="mt-4 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700"
                      >
                        保存编辑
                      </button>
                    </div>
                  )}
                </div>
              )}

              {(draftMessage || draftError) && (
                <p
                  className={`mt-4 text-xs ${
                    draftError
                      ? "text-red-600 dark:text-red-400"
                      : "text-green-700 dark:text-green-300"
                  }`}
                >
                  {draftError || draftMessage}
                </p>
              )}
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
                      拒绝
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
                      批准发布
                    </button>
                  </div>
                </div>

                {reviewError && (
                  <p className="mt-3 text-xs text-red-600 dark:text-red-400">{reviewError}</p>
                )}
              </div>

              <div className="mb-3 flex items-center gap-2">
                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">模拟</span>
                <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">
                  Mock Publish — 模拟发布
                </h3>
              </div>
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
                  {isPublishing ? "正在模拟发布…" : "运行 Mock Publish"}
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
