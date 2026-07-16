import { Heart } from "lucide-react";
import { useNowPlaying } from "../../hooks/use-now-playing";
import { useFavorites, useAddFavorite } from "../../hooks/use-favorites";
import { useAuthStore } from "../../hooks/use-auth-store";
import { fmtMs } from "../../lib/utils";
import ProgressBar from "../../components/ui/ProgressBar";
import Skeleton from "../../components/ui/Skeleton";
import { useToast } from "../../components/ui/Toast";

export default function NowPlayingCard() {
  const { data, isLoading } = useNowPlaying();
  const userId = useAuthStore((s) => s.userId ?? "");
  const { data: favs } = useFavorites(userId);
  const addFav = useAddFavorite(userId);
  const { toast } = useToast();

  const isFavorited = favs?.favorites?.some(
    (f) => f.uri === data?.uri
  );

  function handleFavorite() {
    if (!data?.title || !data?.uri) return;
    addFav.mutate(
      {
        title: data.title,
        author: data.author ?? "Unknown",
        uri: data.uri,
        identifier: data.uri,
        length: data.length ?? 0,
        artwork_url: data.artwork_url ?? undefined,
      },
      {
        onSuccess: () => toast("Added to favorites", "success"),
        onError: () => toast("Failed to add to favorites", "error"),
      }
    );
  }

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
          className="mb-4 h-40 w-full rounded-lg border border-dark-500 object-cover"
        />
      )}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate text-lg font-medium text-white">{data.title}</h3>
          <p className="truncate text-sm text-dark-300">{data.author}</p>
        </div>
        {userId && (
          <button
            onClick={handleFavorite}
            disabled={isFavorited || addFav.isPending}
            className="mt-1 shrink-0 rounded-[11px] p-2 transition-colors hover:bg-white/10 disabled:opacity-40"
            title={isFavorited ? "Already in favorites" : "Add to favorites"}
          >
            <Heart
              className={`h-5 w-5 ${isFavorited ? "fill-accent-fuchsia text-accent-fuchsia" : "text-dark-400"}`}
            />
          </button>
        )}
      </div>
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
