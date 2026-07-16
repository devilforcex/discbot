import { useQuery } from "@tanstack/react-query";
import type { FavoritesResponse } from "../lib/types";
import { api } from "../lib/api-client";

export function useFavorites(userId: string, page = 1) {
  return useQuery<FavoritesResponse>({
    queryKey: ["favorites", userId, page],
    queryFn: () => api.get(`/api/favorites/${userId}?page=${page}`),
    enabled: !!userId,
  });
}
