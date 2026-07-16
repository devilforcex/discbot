import { useQuery } from "@tanstack/react-query";
import type { StatsResponse } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useStats() {
  const guildId = useAuthStore((s) => s.guildId);

  return useQuery<StatsResponse>({
    queryKey: ["stats", guildId],
    queryFn: () => api.get(`/api/stats/${guildId}`),
    enabled: !!guildId,
    refetchInterval: 5000,
  });
}
