import PageHeader from "../components/shared/PageHeader";
import StatsOverview from "../features/statistics/StatsOverview";
import TopTracks from "../features/statistics/TopTracks";
import HistoryList from "../features/statistics/HistoryList";

export default function StatisticsPage() {
  return (
    <div>
      <PageHeader title="Statistics" description="Play history and top tracks" />
      <StatsOverview />
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TopTracks />
        <HistoryList />
      </div>
    </div>
  );
}
