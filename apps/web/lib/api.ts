/**
 * API client for communicating with the backend.
 *
 * Usage:
 *   import { api } from "@/lib/api";
 *   const project = await api.createProject({ title: "...", source_text: "..." });
 */

import type {
  AgentPreviewResponse,
  AgentRun,
  AgentStep,
  EvaluationReportResponse,
  GeneratePreviewRequest,
  PublishPackageResponse,
  ProjectResponse,
  PublishProjectRequest,
  PublishProjectResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface ApiResponse<T> {
  data: T;
  status: number;
}

interface ApiErrorPayload {
  code?: string;
  message: string;
  details?: unknown;
}

interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  error: ApiErrorPayload | null;
}

function isApiEnvelope<T>(body: unknown): body is ApiEnvelope<T> {
  return (
    typeof body === "object" &&
    body !== null &&
    "success" in body &&
    "data" in body &&
    "error" in body
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeErrorPayload(body: unknown, fallbackMessage: string): ApiErrorPayload {
  if (isApiEnvelope<unknown>(body) && body.error) {
    return body.error;
  }

  if (!isRecord(body)) {
    return { message: fallbackMessage };
  }

  const detail = body.detail;
  if (isRecord(detail)) {
    return {
      code: typeof detail.code === "string" ? detail.code : undefined,
      message: typeof detail.message === "string" ? detail.message : fallbackMessage,
      details: "details" in detail ? detail.details : undefined,
    };
  }

  if (Array.isArray(detail)) {
    return {
      code: "VALIDATION_ERROR",
      message: "Request validation failed",
      details: { errors: detail },
    };
  }

  if (typeof detail === "string") {
    return { message: detail };
  }

  return { message: fallbackMessage };
}

function summarizeDetails(details: unknown): string {
  if (!details) {
    return "";
  }

  if (isRecord(details) && Array.isArray(details.errors)) {
    const messages = details.errors
      .map((error) => {
        if (!isRecord(error)) {
          return "";
        }
        const location = Array.isArray(error.loc) ? error.loc.join(".") : "";
        const message = typeof error.msg === "string" ? error.msg : "";
        return [location, message].filter(Boolean).join(": ");
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  if (typeof details === "string") {
    return details;
  }

  try {
    return JSON.stringify(details);
  } catch {
    return "";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${path}`;
  let response: Response;

  try {
    response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : "Network request failed";
    throw new ApiError(
      0,
      "无法连接到后端服务，或浏览器跨域请求被阻止",
      "NETWORK_ERROR",
      { url, reason },
    );
  }

  const responseBody = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    const errorPayload = normalizeErrorPayload(responseBody, response.statusText);
    throw new ApiError(
      response.status,
      errorPayload.message,
      errorPayload.code,
      errorPayload.details ?? null,
    );
  }

  if (isApiEnvelope<T>(responseBody)) {
    if (!responseBody.success || responseBody.data === null) {
      throw new ApiError(
        response.status,
        responseBody.error?.message ?? "API response did not include data",
        responseBody.error?.code,
        responseBody.error?.details ?? null,
      );
    }
    return {
      data: responseBody.data,
      status: response.status,
    };
  }

  return {
    data: responseBody as T,
    status: response.status,
  };
}

async function requestText(path: string, options: RequestInit = {}): Promise<ApiResponse<string>> {
  const url = `${API_BASE_URL}${path}`;
  let response: Response;

  try {
    response = await fetch(url, {
      headers: {
        ...options.headers,
      },
      ...options,
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : "Network request failed";
    throw new ApiError(
      0,
      "无法连接到后端服务，或浏览器跨域请求被阻止",
      "NETWORK_ERROR",
      { url, reason },
    );
  }

  const responseText = await response.text();
  if (!response.ok) {
    let parsedBody: unknown = null;
    try {
      parsedBody = JSON.parse(responseText);
    } catch {
      parsedBody = null;
    }
    const errorPayload = normalizeErrorPayload(parsedBody, response.statusText);
    throw new ApiError(
      response.status,
      errorPayload.message,
      errorPayload.code,
      errorPayload.details ?? null,
    );
  }

  return {
    data: responseText,
    status: response.status,
  };
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof ApiError) {
    const statusText = error.status === 0 ? "网络错误" : `HTTP ${error.status}`;
    const codeText = error.code ? ` / ${error.code}` : "";
    const detailText = summarizeDetails(error.details);
    return detailText
      ? `${statusText}${codeText}: ${error.message}；${detailText}`
      : `${statusText}${codeText}: ${error.message}`;
  }

  if (error instanceof Error && error.message) {
    return `${fallbackMessage}: ${error.message}`;
  }

  return fallbackMessage;
}

export const api = {
  get<T>(path: string): Promise<ApiResponse<T>> {
    return request<T>(path, { method: "GET" });
  },

  post<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    return request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  put<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    return request<T>(path, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  delete<T>(path: string): Promise<ApiResponse<T>> {
    return request<T>(path, { method: "DELETE" });
  },

  publishProject(
    projectId: string,
    body: PublishProjectRequest,
  ): Promise<ApiResponse<PublishProjectResponse>> {
    return request<PublishProjectResponse>(`/api/projects/${projectId}/publish`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  generateAgentPreview(
    projectId: string,
    body: GeneratePreviewRequest,
  ): Promise<ApiResponse<AgentPreviewResponse>> {
    return request<AgentPreviewResponse>(`/api/projects/${projectId}/agent-preview`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getAgentRun(runId: string): Promise<ApiResponse<AgentRun>> {
    return request<AgentRun>(`/api/runs/${runId}`, {
      method: "GET",
    });
  },

  listAgentSteps(runId: string): Promise<ApiResponse<AgentStep[]>> {
    return request<AgentStep[]>(`/api/runs/${runId}/steps`, {
      method: "GET",
    });
  },

  createEvaluation(projectId: string): Promise<ApiResponse<EvaluationReportResponse>> {
    return request<EvaluationReportResponse>(`/api/projects/${projectId}/evaluation`, {
      method: "POST",
    });
  },

  getEvaluation(projectId: string): Promise<ApiResponse<EvaluationReportResponse>> {
    return request<EvaluationReportResponse>(`/api/projects/${projectId}/evaluation`, {
      method: "GET",
    });
  },

  getPublishPackage(projectId: string): Promise<ApiResponse<PublishPackageResponse>> {
    return request<PublishPackageResponse>(`/api/projects/${projectId}/export/json`, {
      method: "GET",
    });
  },

  getPublishPackageMarkdown(projectId: string): Promise<ApiResponse<string>> {
    return requestText(`/api/projects/${projectId}/export/markdown`, {
      method: "GET",
    });
  },

  approveProject(projectId: string): Promise<ApiResponse<ProjectResponse>> {
    return request<ProjectResponse>(`/api/projects/${projectId}/review/approve`, {
      method: "POST",
    });
  },

  rejectProject(projectId: string): Promise<ApiResponse<ProjectResponse>> {
    return request<ProjectResponse>(`/api/projects/${projectId}/review/reject`, {
      method: "POST",
    });
  },
};
