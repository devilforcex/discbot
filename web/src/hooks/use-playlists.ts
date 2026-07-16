import { useQuery } from "@tanstack/react-query";
import type { PlaylistsResponse } from "../lib/types";
import { api } from "../lib/api-client";

export function usePlaylists(userId: string) {
  return useQuery<PlaylistsResponse>({
    queryKey: ["playlists", userId],
    queryFn: () => api.get(`/api/playlists/${userId}`),
    enabled: !!userId,
  });
}
