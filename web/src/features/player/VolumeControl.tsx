import { useCallback, useState } from "react";
import { useControl } from "../../hooks/use-control";
import { useNowPlaying } from "../../hooks/use-now-playing";
import Slider from "../../components/ui/Slider";

export default function VolumeControl() {
  const { data } = useNowPlaying();
  const control = useControl();
  const [volume, setVolume] = useState(data?.volume ?? 50);

  const handleChange = useCallback(
    (val: number) => {
      setVolume(val);
      control.mutate({ action: "volume", body: { volume: val } });
    },
    [control],
  );

  return (
    <Slider
      value={volume}
      onChange={handleChange}
      min={0}
      max={100}
      label="Volume"
    />
  );
}
