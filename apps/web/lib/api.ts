/**
 * API client for communicating with the backend.
 *
 * Usage:
 *   import { api } from "@/lib/api";
 *   const project = await api.createProject({ title: "...", source_text: "..." });
 */

import type {
  EvaluationReportResponse,
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
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
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

async function request<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const responseBody = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    if (isApiEnvelope<T>(responseBody) && responseBody.error) {
      throw new ApiError(
        response.status,
        responseBody.error.message,
        responseBody.error.code,
        responseBody.error.details ?? null,
      );
    }
    throw new ApiError(response.status, response.statusText);
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

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public details?: Record<string, unknown> | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
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
