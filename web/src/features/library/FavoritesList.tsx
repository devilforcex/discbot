import { useFavorites } from "../../hooks/use-favorites";
import { fmtMs } from "../../lib/utils";
import EmptyState from "../../components/ui/EmptyState";
import Skeleton from "../../components/ui/Skeleton";
import { Heart } from "lucide-react";

interface FavoritesListProps {
  userId: string;
}

export default function FavoritesList({ userId }: FavoritesListProps) {
  const { data, isLoading } = useFavorites(userId);

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
            className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-dark-600 transition-colors"
          >
            <div className="min-w-0 flex-1">
              <div className="truncate text-dark-100">{fav.title}</div>
              <div className="truncate text-xs text-dark-400">{fav.author}</div>
            </div>
            <span className="ml-3 text-xs text-dark-400">{fmtMs(fav.length)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
