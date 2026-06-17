"use client";

import { useHealth } from "@/hooks/useHealth";

/**
 * Displays the backend health check status.
 * Useful for verifying the API connection during development.
 */
export function HealthStatus() {
  const { data, loading, error } = useHealth();

  if (loading) {
    return <div className="text-sm text-gray-400">Checking backend connection...</div>;
  }

  if (error) {
    return <div className="text-sm text-red-500">Backend unavailable: {error}</div>;
  }

  if (data) {
    return (
      <div className="text-sm text-green-600 dark:text-green-400">
        Backend connected &mdash; {data.service} ({data.status})
      </div>
    );
  }

  return null;
}
