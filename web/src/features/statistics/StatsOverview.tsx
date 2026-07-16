import { useStats } from "../../hooks/use-stats";
import StatCard from "../../components/ui/StatCard";
import { BarChart3, Music } from "lucide-react";
import Skeleton from "../../components/ui/Skeleton";

export default function StatsOverview() {
  const { data, isLoading } = useStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <StatCard
        icon={<BarChart3 className="h-4 w-4" />}
        label="Total Plays"
        value={data?.total_plays ?? 0}
      />
      <StatCard
        icon={<Music className="h-4 w-4" />}
        label="Unique Tracks"
        value={data?.unique_tracks ?? 0}
      />
    </div>
  );
}
