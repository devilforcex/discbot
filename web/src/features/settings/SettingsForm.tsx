import { useSettings, useUpdateSettings } from "../../hooks/use-settings";
import { useAuthStore } from "../../hooks/use-auth-store";
import Toggle from "../../components/ui/Toggle";
import Select from "../../components/ui/Select";
import Slider from "../../components/ui/Slider";
import Button from "../../components/ui/Button";
import TokenInput from "../../components/shared/TokenInput";
import GlassCard from "../../components/ui/GlassCard";
import Skeleton from "../../components/ui/Skeleton";
import { useState, useEffect } from "react";

export default function SettingsForm() {
  const guildId = useAuthStore((s) => s.guildId);
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();

  const [volume, setVolume] = useState(50);
  const [defaultSource, setDefaultSource] = useState("ytsearch");
  const [autoplay, setAutoplay] = useState(true);
  const [announceSongs, setAnnounceSongs] = useState(true);

  useEffect(() => {
    if (settings) {
      setVolume(settings.volume);
      setDefaultSource(settings.default_source);
      setAutoplay(settings.autoplay);
      setAnnounceSongs(settings.announce_songs);
    }
  }, [settings]);

  if (!guildId) {
    return (
      <GlassCard>
        <p className="text-sm text-dark-400">Select a guild to manage settings.</p>
      </GlassCard>
    );
  }

  if (isLoading) {
    return (
      <GlassCard>
        <Skeleton className="mb-4 h-8 w-full" />
        <Skeleton className="mb-4 h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </GlassCard>
    );
  }

  const handleSave = () => {
    updateSettings.mutate({
      volume,
      default_source: defaultSource,
      autoplay,
      announce_songs: announceSongs,
    });
  };

  return (
    <GlassCard className="space-y-6">
      <TokenInput />

      <Slider
        value={volume}
        onChange={setVolume}
        min={0}
        max={100}
        label="Default Volume"
      />

      <Select
        label="Default Source"
        value={defaultSource}
        onChange={(e) => setDefaultSource(e.target.value)}
        options={[
          { value: "ytsearch", label: "YouTube" },
          { value: "ytmsearch", label: "YouTube Music" },
          { value: "scsearch", label: "SoundCloud" },
        ]}
      />

      <Toggle
        label="Autoplay recommendations"
        checked={autoplay}
        onChange={setAutoplay}
      />

      <Toggle
        label="Announce songs in text channel"
        checked={announceSongs}
        onChange={setAnnounceSongs}
      />

      <div className="flex gap-3">
        <Button onClick={handleSave} disabled={updateSettings.isPending}>
          {updateSettings.isPending ? "Saving..." : "Save Settings"}
        </Button>
        <Button variant="ghost" onClick={() => window.location.reload()}>
          Refresh
        </Button>
      </div>

      {updateSettings.isSuccess && (
        <p className="text-sm text-accent-emerald">Settings saved!</p>
      )}
      {updateSettings.isError && (
        <p className="text-sm text-accent-red">Failed to save settings.</p>
      )}
    </GlassCard>
  );
}
