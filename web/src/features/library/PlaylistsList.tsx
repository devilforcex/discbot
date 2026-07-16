import { usePlaylists } from "../../hooks/use-playlists";
import EmptyState from "../../components/ui/EmptyState";
import Skeleton from "../../components/ui/Skeleton";
import { ListMusic } from "lucide-react";

interface PlaylistsListProps {
  userId: string;
}

export default function PlaylistsList({ userId }: PlaylistsListProps) {
  const { data, isLoading } = usePlaylists(userId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    );
  }

  if (!data?.playlists.length) {
    return (
      <EmptyState
        icon={<ListMusic className="h-8 w-8" />}
        title="No playlists"
        description="Use !playlist_create in Discord"
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {data.playlists.map((pl) => (
        <div
          key={pl.playlist_id}
          className="glass rounded-xl p-4 transition-all hover:bg-dark-600"
        >
          <h4 className="font-medium text-dark-100">{pl.name}</h4>
          {pl.description && (
            <p className="mt-1 text-xs text-dark-400">{pl.description}</p>
          )}
          <p className="mt-2 text-xs text-dark-500">
            {pl.track_count} tracks
          </p>
        </div>
      ))}
    </div>
  );
}
