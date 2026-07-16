import { useFavorites, useRemoveFavorite } from "../../hooks/use-favorites";
import { useControl } from "../../hooks/use-control";
import { useToast } from "../../components/ui/Toast";
import { fmtMs } from "../../lib/utils";
import EmptyState from "../../components/ui/EmptyState";
import Skeleton from "../../components/ui/Skeleton";
import { Heart, Play, Trash2 } from "lucide-react";

interface FavoritesListProps {
  userId: string;
}

export default function FavoritesList({ userId }: FavoritesListProps) {
  const { data, isLoading } = useFavorites(userId);
  const removeFav = useRemoveFavorite(userId);
  const control = useControl();
  const { toast } = useToast();

  const handlePlay = (uri: string) => {
    control.mutate(
      { action: "play_pause", body: { uri } },
      { onError: () => toast("Failed to play track.", "error") },
    );
  };

  const handleRemove = (identifier: string) => {
    removeFav.mutate(identifier, {
      onSuccess: () => toast("Removed from favorites.", "success"),
      onError: () => toast("Failed to remove favorite.", "error"),
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.favorites.length) {
    return (
      <EmptyState
        icon={<Heart className="h-8 w-8" />}
        title="No favorites"
        description="Use !favorite in Discord to save tracks"
      />
    );
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="mb-3 text-sm font-medium text-dark-100">
        Favorites ({data.total})
      </h3>
      <div className="space-y-1">
        {data.favorites.map((fav, i) => (
          <div
            key={`${fav.uri}-${i}`}
            className="group flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-dark-600 transition-colors"
          >
            <div className="min-w-0 flex-1">
              <div className="truncate text-dark-100">{fav.title}</div>
              <div className="truncate text-xs text-dark-400">{fav.author}</div>
            </div>
            <div className="ml-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {fav.uri && (
                <button
                  onClick={() => handlePlay(fav.uri)}
                  className="rounded p-1 text-dark-400 hover:text-accent-violet transition-colors"
                  title="Play"
                >
                  <Play className="h-3.5 w-3.5" />
                </button>
              )}
              {fav.identifier && (
                <button
                  onClick={() => handleRemove(fav.identifier!)}
                  disabled={removeFav.isPending}
                  className="rounded p-1 text-dark-400 hover:text-accent-red transition-colors"
                  title="Remove"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            <span className="ml-3 text-xs text-dark-400">{fmtMs(fav.length)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
