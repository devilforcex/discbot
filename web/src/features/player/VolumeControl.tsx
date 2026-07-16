import { useCallback, useEffect, useRef, useState } from "react";
import { useControl } from "../../hooks/use-control";
import { useNowPlaying } from "../../hooks/use-now-playing";
import Slider from "../../components/ui/Slider";

export default function VolumeControl() {
  const { data } = useNowPlaying();
  const control = useControl();
  const [volume, setVolume] = useState(data?.volume ?? 50);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (data?.volume !== undefined) {
      setVolume(data.volume);
    }
  }, [data?.volume]);

  const handleChange = useCallback(
    (val: number) => {
      setVolume(val);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        if (mountedRef.current) {
          control.mutate({ action: "volume", body: { volume: val } });
        }
      }, 300);
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
