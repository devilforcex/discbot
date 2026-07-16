import { Play, Pause, SkipForward, Square, Shuffle } from "lucide-react";
import { useControl } from "../../hooks/use-control";
import { useNowPlaying } from "../../hooks/use-now-playing";
import { useToast } from "../../components/ui/Toast";
import Button from "../../components/ui/Button";

export default function PlayerControls() {
  const { data } = useNowPlaying();
  const control = useControl();
  const { toast } = useToast();

  const handle = (action: "play_pause" | "skip" | "stop" | "shuffle") => {
    control.mutate(
      { action },
      { onError: () => toast("Control action failed.", "error") },
    );
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handle("play_pause")}
        disabled={control.isPending}
      >
        {data?.paused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handle("skip")}
        disabled={control.isPending}
      >
        <SkipForward className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handle("stop")}
        disabled={control.isPending}
      >
        <Square className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handle("shuffle")}
        disabled={control.isPending}
      >
        <Shuffle className="h-4 w-4" />
      </Button>
    </div>
  );
}
