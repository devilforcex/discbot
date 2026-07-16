import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { PlaylistsResponse, PlaylistDetail } from "../lib/types";
import { api } from "../lib/api-client";

export function usePlaylists(userId: string) {
  return useQuery<PlaylistsResponse>({
    queryKey: ["playlists", userId],
    queryFn: () => api.get(`/api/playlists/${userId}`),
    enabled: !!userId,
  });
}

export function usePlaylistDetail(userId: string, playlistId: string) {
  return useQuery<PlaylistDetail>({
    queryKey: ["playlist", userId, playlistId],
    queryFn: () => api.get(`/api/playlists/${userId}/${playlistId}`),
    enabled: !!userId && !!playlistId,
  });
}

export function useCreatePlaylist(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; guild_id?: string }) =>
      api.post(`/api/playlists/${userId}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playlists", userId] }),
  });
}

export function useDeletePlaylist(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (playlistId: string) =>
      api.delete(`/api/playlists/${playlistId}`, { user_id: userId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playlists", userId] }),
  });
}

export function useAddPlaylistTrack(userId: string, playlistId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (track: { title: string; author: string; uri: string; identifier: string; length: number; artwork_url?: string }) =>
      api.post(`/api/playlists/${playlistId}/tracks`, { ...track, added_by: userId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playlist", userId, playlistId] }),
  });
}

export function useRemovePlaylistTrack(userId: string, playlistId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (position: number) =>
      api.delete(`/api/playlists/${playlistId}/tracks/${position}`, { user_id: userId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playlist", userId, playlistId] }),
  });
}
