import { Server, Zap, Users, Music } from "lucide-react";
import StatCard from "../../components/ui/StatCard";
import { useStatus } from "../../hooks/use-status";
import { useHealth } from "../../hooks/use-health";
import { useQueue } from "../../hooks/use-queue";
import { useAuthStore } from "../../hooks/use-auth-store";
import { fmtNumber } from "../../lib/utils";

export default function OverviewGrid() {
  const { data: status } = useStatus();
  const { data: health } = useHealth();
  const guildId = useAuthStore((s) => s.guildId);
  const { data: queue } = useQueue();

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        icon={<Server className="h-4 w-4" />}
        label="Bot Status"
        value={health?.ready ? "Online" : "Offline"}
        sub={status?.bot_name}
      />
      <StatCard
        icon={<Zap className="h-4 w-4" />}
        label="Latency"
        value={status?.latency_ms != null ? `${Math.round(status.latency_ms)}ms` : "—"}
      />
      <StatCard
        icon={<Users className="h-4 w-4" />}
        label="Guilds"
        value={fmtNumber(status?.guild_count)}
        sub={`${status?.connected_voice_channels ?? 0} voice channels`}
      />
      <StatCard
        icon={<Music className="h-4 w-4" />}
        label="Queue"
        value={guildId ? (queue?.queue_length ?? 0) : "—"}
        sub={guildId ? "tracks" : "select a guild"}
      />
    </div>
  );
}
