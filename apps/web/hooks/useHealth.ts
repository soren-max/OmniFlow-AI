/**
 * Hook for checking backend health status.
 *
 * Usage:
 *   const { data, loading, error } = useHealth();
 */

"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { HealthResponse } from "@/types";

interface UseHealthResult {
  data: HealthResponse | null;
  loading: boolean;
  error: string | null;
}

export function useHealth(): UseHealthResult {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const response = await api.get<HealthResponse>("/health");
        if (!cancelled) {
          setData(response.data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? `API Error (${err.status}): ${err.message}`
              : "Failed to connect to backend",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    check();

    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}
