import { useStats } from "../../hooks/use-stats";
import EmptyState from "../../components/ui/EmptyState";
import { Trophy } from "lucide-react";

export default function TopTracks() {
  const { data } = useStats();

  if (!data?.top_tracks.length) {
    return <EmptyState icon={<Trophy className="h-8 w-8" />} title="No tracks played yet" />;
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="mb-3 text-sm font-medium text-dark-100">Top Tracks</h3>
      <div className="space-y-2">
        {data.top_tracks.map((track, i) => (
          <div
            key={`${track.title}-${i}`}
            className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-dark-600 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="w-6 text-center text-xs font-bold text-dark-400">
                {i + 1}
              </span>
              <div className="min-w-0">
                <div className="truncate text-dark-100">{track.title}</div>
                <div className="truncate text-xs text-dark-400">{track.author}</div>
              </div>
            </div>
            <span className="text-xs font-medium text-accent-violet">
              {track.play_count} plays
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
