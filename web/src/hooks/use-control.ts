import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ControlAction, ControlResponse } from "../lib/types";
import { api } from "../lib/api-client";
import { useAuthStore } from "./use-auth-store";

export function useControl() {
  const guildId = useAuthStore((s) => s.guildId);
  const queryClient = useQueryClient();

  return useMutation<ControlResponse, Error, { action: ControlAction; body?: unknown }>({
    mutationFn: ({ action, body }) =>
      api.post(`/api/control/${guildId}/${action}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nowplaying", guildId] });
      queryClient.invalidateQueries({ queryKey: ["queue", guildId] });
    },
  });
}
