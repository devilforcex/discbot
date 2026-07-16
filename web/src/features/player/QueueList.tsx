import { useQueue } from "../../hooks/use-queue";
import { fmtMs } from "../../lib/utils";
import EmptyState from "../../components/ui/EmptyState";
import Skeleton from "../../components/ui/Skeleton";
import { ListMusic } from "lucide-react";

export default function QueueList() {
  const { data, isLoading } = useQueue();

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
    return <EmptyState icon={<ListMusic className="h-8 w-8" />} title="Queue is empty" />;
  }

  return (
    <div className="max-h-[400px] space-y-1 overflow-y-auto scrollbar-thin">
      {data.tracks.map((track, i) => (
        <div
          key={`${track.uri}-${i}`}
          className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-dark-600 transition-colors"
        >
          <div className="min-w-0 flex-1">
            <div className="truncate text-dark-100">{track.title ?? "Unknown"}</div>
            <div className="truncate text-xs text-dark-400">{track.author ?? "Unknown"}</div>
          </div>
          <span className="ml-3 text-xs text-dark-400">{fmtMs(track.length)}</span>
        </div>
      ))}
    </div>
  );
}
