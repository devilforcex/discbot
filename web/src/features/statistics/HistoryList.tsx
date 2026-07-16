import { useHistory } from "../../hooks/use-history";
import { fmtMs } from "../../lib/utils";
import EmptyState from "../../components/ui/EmptyState";
import Skeleton from "../../components/ui/Skeleton";
import { Clock } from "lucide-react";

export default function HistoryList() {
  const { data, isLoading } = useHistory(20);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.tracks.length) {
    return (
      <EmptyState
        icon={<Clock className="h-8 w-8" />}
        title="No history"
      />
    );
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="mb-3 text-sm font-medium text-dark-100">Recent History</h3>
      <div className="max-h-[400px] space-y-1 overflow-y-auto scrollbar-thin">
        {data.tracks.map((track, i) => (
          <div
            key={`${track.uri}-${i}`}
            className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-dark-600 transition-colors"
          >
            <div className="min-w-0 flex-1">
              <div className="truncate text-dark-100">{track.title}</div>
              <div className="truncate text-xs text-dark-400">{track.author}</div>
            </div>
            <div className="ml-3 text-right">
              <div className="text-xs text-dark-400">{fmtMs(track.length)}</div>
              {track.played_at && (
                <div className="text-[10px] text-dark-500">
                  {new Date(track.played_at).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
