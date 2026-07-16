import { useQuery } from "@tanstack/react-query";
import type { HealthResponse, LavalinkHealthResponse } from "../lib/types";
import { api } from "../lib/api-client";

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => api.get("/api/health"),
    refetchInterval: 10000,
  });
}

export function useLavalinkHealth() {
  return useQuery<LavalinkHealthResponse>({
    queryKey: ["health", "lavalink"],
    queryFn: () => api.get("/api/health/lavalink"),
    refetchInterval: 10000,
  });
}
