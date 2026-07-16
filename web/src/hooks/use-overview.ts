import { useQuery } from "@tanstack/react-query";
import type { OverviewResponse } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useOverview() {
  const guildId = useAuthStore((s) => s.guildId);

  return useQuery<OverviewResponse>({
    queryKey: ["overview", guildId],
    queryFn: () => api.get(`/api/overview/${guildId}`),
    enabled: !!guildId,
    refetchInterval: 10000,
  });
}
