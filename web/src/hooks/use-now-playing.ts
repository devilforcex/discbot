import { useQuery } from "@tanstack/react-query";
import type { NowPlayingResponse } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useNowPlaying() {
  const guildId = useAuthStore((s) => s.guildId);

  return useQuery<NowPlayingResponse>({
    queryKey: ["nowplaying", guildId],
    queryFn: () => api.get(`/api/nowplaying/${guildId}`),
    enabled: !!guildId,
    refetchInterval: 3000,
  });
}
