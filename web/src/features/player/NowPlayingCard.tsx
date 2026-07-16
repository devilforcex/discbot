import { useNowPlaying } from "../../hooks/use-now-playing";
import { fmtMs } from "../../lib/utils";
import ProgressBar from "../../components/ui/ProgressBar";
import Skeleton from "../../components/ui/Skeleton";

export default function NowPlayingCard() {
  const { data, isLoading } = useNowPlaying();

  if (isLoading) {
    return (
      <div className="glass rounded-xl p-6">
        <Skeleton className="mb-4 h-40 w-full" />
        <Skeleton className="mb-2 h-5 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
      </div>
    );
  }

  if (!data?.playing) {
    return (
      <div className="glass rounded-xl p-6 text-center">
        <div className="text-dark-400">Nothing playing</div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-6">
      {data.artwork_url && (
        <img
          src={data.artwork_url}
          alt={data.title}
          className="mb-4 h-40 w-full rounded-lg object-cover"
        />
      )}
      <h3 className="truncate text-lg font-medium text-white">{data.title}</h3>
      <p className="truncate text-sm text-dark-300">{data.author}</p>
      <div className="mt-4">
        <ProgressBar value={data.position ?? 0} max={data.length ?? 1} />
        <div className="mt-1 flex justify-between text-xs text-dark-400">
          <span>{fmtMs(data.position)}</span>
          <span>{fmtMs(data.length)}</span>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-dark-400">
        <span>🔊 {data.volume ?? 50}%</span>
        {data.autoplay && <span>🤖 Autoplay</span>}
        {data.loop && <span>🔁 {data.loop}</span>}
      </div>
    </div>
  );
}
