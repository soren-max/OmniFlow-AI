/**
 * Shared type definitions for the frontend.
 *
 * These types mirror the backend API schemas.
 * In a future stage, they might be auto-generated from OpenAPI specs.
 */

/** Health check response from the backend */
export interface HealthResponse {
  status: string;
  service: string;
}

/** Supported platforms */
export type Platform = "wechat" | "zhihu" | "bilibili" | "xiaohongshu" | "douyin";

/** Content status */
export type ContentStatus =
  | "draft"
  | "pending"
  | "adapted"
  | "reviewing"
  | "approved"
  | "rejected"
  | "published";

/** Human review status used by the current API gate */
export type ReviewStatus = "pending" | "approved" | "rejected";

/** Agent run status */
export type AgentRunStatus = "pending" | "running" | "completed" | "failed";

/** Persisted Agent Run trace record */
export interface AgentRun {
  run_id: string;
  project_id: string;
  workflow_name: string;
  status: AgentRunStatus;
  started_at?: string;
  finished_at?: string | null;
  total_latency_ms?: number | null;
  error_message?: string | null;
}

/** Persisted Agent Step trace record */
export interface AgentStep {
  step_id: string;
  run_id: string;
  node_name: string;
  status: AgentRunStatus;
  latency_ms?: number | null;
  error_message?: string | null;
  started_at?: string;
  finished_at?: string | null;
}

/** Evaluation scores */
export interface EvaluationScores {
  format_score: number;
  style_score: number;
  consistency_score: number;
  compliance_score: number;
  completeness_score: number;
  overall_score: number;
}

// ── Project API types ─────────────────────────────────────────────────────────

/** Request body for creating a content project */
export interface CreateProjectRequest {
  title: string;
  source_text: string;
  source_url?: string;
}

/** A single platform preview item in the response */
export interface ProjectPreviewItem {
  project_id: string;
  platform: string;
  platform_display_name: string;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
  preview: Record<string, unknown>;
  validation: Record<string, unknown>;
  rendered_html: string;
  word_count: number;
  estimated_read_time_min: number;
  warnings: string[];
}

/** Response from creating or getting a project */
export interface ProjectResponse {
  id: string;
  title: string;
  source_text: string;
  source_url: string | null;
  status: string;
  created_at: string;
  previews: ProjectPreviewItem[];
}

/** Request body for generating previews */
export interface GeneratePreviewRequest {
  platforms: string[];
  title?: string;
  hooks?: string[];
  tags?: string[];
}

/** Response from generating previews */
export interface GeneratePreviewResponse {
  project_id: string;
  project_title: string;
  previews: ProjectPreviewItem[];
  generated_at: string;
}

/** Response from the deterministic Agent preview workflow */
export interface AgentPreviewResponse {
  run_id: string | null;
  project_id: string;
  source_title: string;
  source_content: string;
  target_platforms: string[];
  status: string;
  errors: string[];
  previews: Record<string, ProjectPreviewItem>;
}

/** Request body for mock publishing a project */
export interface PublishProjectRequest {
  target_platforms: string[];
  mode: "mock" | "real";
}

/** A single platform publish result */
export interface PlatformPublishResultItem {
  platform: string;
  platform_display_name: string;
  status: string;
  mock_url: string | null;
  message: string;
  metadata: Record<string, unknown>;
}

/** Response from mock publishing a project */
export interface PublishProjectResponse {
  project_id: string;
  mode: string;
  results: PlatformPublishResultItem[];
  published_at: string;
}

/** Rule-based platform evaluation score */
export interface PlatformEvaluationScore extends EvaluationScores {
  platform: string;
  platform_display_name: string;
  issues: string[];
  suggestions: string[];
}

/** Rule-based evaluation report */
export interface EvaluationReportResponse {
  project_id: string;
  average_score: number;
  platform_scores: PlatformEvaluationScore[];
  issues: string[];
  suggestions: string[];
  created_at: string;
}

/** Export-ready content for one platform */
export interface PublishPackagePlatformContent {
  platform: string;
  title: string;
  body: string;
  hashtags: string[];
  summary: string;
  cta: string;
  notes: string;
  copy_text: string;
}

/** Evaluation summary included in publish package exports */
export interface PublishPackageEvaluationSummary {
  average_score: number | null;
  issues: string[];
  suggestions: string[];
  message?: string | null;
}

/** Manual publish package export */
export interface PublishPackageResponse {
  project_id: string;
  title: string;
  created_at: string;
  platforms: string[];
  platform_contents: PublishPackagePlatformContent[];
  review_status: string;
  package_status: string;
  warnings: string[];
  evaluation_summary: PublishPackageEvaluationSummary;
  exported_at: string;
}

/** Platform display info */
export interface PlatformOption {
  id: Platform;
  label: string;
  description: string;
  color: string;
}

/** Platform options for the selector */
export const PLATFORM_OPTIONS: PlatformOption[] = [
  {
    id: "wechat",
    label: "微信公众号",
    description: "长文、正式、富文本风格",
    color: "#07c160",
  },
  {
    id: "zhihu",
    label: "知乎",
    description: "理性分析、结构化文章",
    color: "#0084ff",
  },
  {
    id: "bilibili",
    label: "B站",
    description: "视频脚本、口播风格",
    color: "#fb7299",
  },
  {
    id: "xiaohongshu",
    label: "小红书",
    description: "种草风、短段落、emoji",
    color: "#ff2442",
  },
  {
    id: "douyin",
    label: "抖音",
    description: "短视频脚本、前三秒 Hook、分镜建议和互动引导",
    color: "#111111",
  },
];
