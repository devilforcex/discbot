import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { GuildSettings, SettingsUpdate } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useSettings() {
  const guildId = useAuthStore((s) => s.guildId);

  return useQuery<GuildSettings>({
    queryKey: ["settings", guildId],
    queryFn: () => api.get(`/api/settings/${guildId}`),
    enabled: !!guildId,
    refetchInterval: 30000,
  });
}

export function useUpdateSettings() {
  const guildId = useAuthStore((s) => s.guildId);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (update: SettingsUpdate) =>
      api.post<{ success: boolean; settings: GuildSettings }>(
        `/api/settings/${guildId}`,
        update,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", guildId] });
    },
  });
}
