/**
 * @contentops/shared
 *
 * Shared types and utilities used across frontend and backend.
 * In future stages, this package will contain:
 * - Platform enum and types
 * - Content status types
 * - Shared validation logic
 */

export type Platform = "wechat" | "zhihu" | "bilibili" | "xiaohongshu";

export type ContentStatus =
  | "draft"
  | "adapted"
  | "reviewing"
  | "approved"
  | "rejected"
  | "published";

export type AgentRunStatus = "pending" | "running" | "completed" | "failed";
