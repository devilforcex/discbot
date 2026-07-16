import { useQuery } from "@tanstack/react-query";
import type { QueueResponse } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useQueue() {
  const guildId = useAuthStore((s) => s.guildId);

  return useQuery<QueueResponse>({
    queryKey: ["queue", guildId],
    queryFn: () => api.get(`/api/queue/${guildId}`),
    enabled: !!guildId,
    refetchInterval: 3000,
  });
}
