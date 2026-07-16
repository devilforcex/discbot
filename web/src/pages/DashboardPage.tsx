import PageHeader from "../components/shared/PageHeader";
import OverviewGrid from "../features/dashboard/OverviewGrid";
import QuickApiLinks from "../features/dashboard/QuickApiLinks";

export default function DashboardPage() {
  return (
    <div>
      <PageHeader title="Overview" description="Bot status and quick stats" />
      <OverviewGrid />
      <QuickApiLinks />
    </div>
  );
}
