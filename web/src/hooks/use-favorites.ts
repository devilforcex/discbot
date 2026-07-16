import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { FavoritesResponse } from "../lib/types";
import { api } from "../lib/api-client";

export function useFavorites(userId: string, page = 1) {
  return useQuery<FavoritesResponse>({
    queryKey: ["favorites", userId, page],
    queryFn: () => api.get(`/api/favorites/${userId}?page=${page}`),
    enabled: !!userId,
  });
}

export function useAddFavorite(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (track: { title: string; author: string; uri: string; identifier: string; length: number; artwork_url?: string }) =>
      api.post(`/api/favorites/${userId}`, track),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["favorites", userId] }),
  });
}

export function useRemoveFavorite(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (identifier: string) =>
      api.delete(`/api/favorites/${userId}/${encodeURIComponent(identifier)}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["favorites", userId] }),
  });
}
