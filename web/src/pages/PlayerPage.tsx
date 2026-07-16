import PageHeader from "../components/shared/PageHeader";
import NowPlayingCard from "../features/player/NowPlayingCard";
import PlayerControls from "../features/player/PlayerControls";
import VolumeControl from "../features/player/VolumeControl";
import QueueList from "../features/player/QueueList";
import GlassCard from "../components/ui/GlassCard";

export default function PlayerPage() {
  return (
    <div>
      <PageHeader title="Player" description="Control music playback" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <NowPlayingCard />
          <GlassCard className="flex items-center justify-between">
            <PlayerControls />
            <div className="w-40">
              <VolumeControl />
            </div>
          </GlassCard>
        </div>
        <GlassCard>
          <h3 className="mb-3 text-sm font-medium text-dark-100">Queue</h3>
          <QueueList />
        </GlassCard>
      </div>
    </div>
  );
}
