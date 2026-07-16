import PageHeader from "../components/shared/PageHeader";
import SettingsForm from "../features/settings/SettingsForm";

export default function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings" description="Manage guild settings" />
      <div className="max-w-2xl">
        <SettingsForm />
      </div>
    </div>
  );
}
