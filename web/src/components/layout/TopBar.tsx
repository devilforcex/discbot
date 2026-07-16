import { Activity, Clock, Menu } from "lucide-react";
import { useStatus } from "../../hooks/use-status";
import StatusBadge from "../ui/StatusBadge";

interface TopBarProps {
  onMenuToggle?: () => void;
}

export default function TopBar({ onMenuToggle }: TopBarProps) {
  const { data: status } = useStatus();

  return (
    <header className="sticky top-0 z-30 flex items-center gap-4 border-b border-glass-border bg-dark-800/80 px-4 py-3 backdrop-blur-md lg:px-6">
      <button
        onClick={onMenuToggle}
        className="rounded-lg p-1.5 text-dark-300 hover:bg-dark-600 lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex flex-1 items-center gap-4">
        <StatusBadge
          label={status?.bot_name ?? "Bot"}
          status={status ? "ok" : "idle"}
        />
      </div>

      <div className="flex items-center gap-4 text-sm text-dark-300">
        {status?.latency_ms != null && (
          <div className="flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            <span>{Math.round(status.latency_ms)}ms</span>
          </div>
        )}
        {status?.uptime && (
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>{status.uptime}</span>
          </div>
        )}
      </div>
    </header>
  );
}
