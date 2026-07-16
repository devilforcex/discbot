import { useQuery } from "@tanstack/react-query";
import type { GuildsResponse } from "../lib/types";
import { api } from "../lib/api-client";

export function useGuilds() {
  return useQuery<GuildsResponse>({
    queryKey: ["guilds"],
    queryFn: () => api.get("/api/guilds"),
    refetchInterval: 30000,
  });
}
