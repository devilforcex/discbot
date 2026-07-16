import { useQuery } from "@tanstack/react-query";
import type { HistoryResponse } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useHistory(limit = 20) {
  const guildId = useAuthStore((s) => s.guildId);

  return useQuery<HistoryResponse>({
    queryKey: ["history", guildId, limit],
    queryFn: () => api.get(`/api/history/${guildId}?limit=${limit}`),
    enabled: !!guildId,
    refetchInterval: 5000,
  });
}
