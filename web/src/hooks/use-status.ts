import { useQuery } from "@tanstack/react-query";
import type { StatusResponse } from "../lib/types";
import { api } from "../lib/api-client";

export function useStatus() {
  return useQuery<StatusResponse>({
    queryKey: ["status"],
    queryFn: () => api.get("/api/status"),
    refetchInterval: 10000,
  });
}
