import { useParams, useNavigate } from "react-router-dom";
import { useAuthStore } from "../hooks/use-auth-store";
import { usePlaylistDetail, useDeletePlaylist, useRemovePlaylistTrack } from "../hooks/use-playlists";
import { useControl } from "../hooks/use-control";
import { useToast } from "../components/ui/Toast";
import { fmtMs } from "../lib/utils";
import PageHeader from "../components/shared/PageHeader";
import GlassCard from "../components/ui/GlassCard";
import Skeleton from "../components/ui/Skeleton";
import Button from "../components/ui/Button";
import { ArrowLeft, Play, Trash2, Music } from "lucide-react";

export default function PlaylistDetailPage() {
  const { playlistId } = useParams<{ playlistId: string }>();
  const userId = useAuthStore((s) => s.userId);
  const navigate = useNavigate();
  const { toast } = useToast();

  const { data: playlist, isLoading } = usePlaylistDetail(userId, playlistId ?? "");
  const deletePlaylist = useDeletePlaylist(userId);
  const removeTrack = useRemovePlaylistTrack(userId, playlistId ?? "");
  const control = useControl();

  const handlePlay = (uri: string) => {
    control.mutate(
      { action: "play_pause", body: { uri } },
      { onError: () => toast("Failed to play track.", "error") },
    );
  };

  const handleRemoveTrack = (position: number) => {
    removeTrack.mutate(position, {
      onSuccess: () => toast("Track removed.", "success"),
      onError: () => toast("Failed to remove track.", "error"),
    });
  };

  const handleDeletePlaylist = () => {
    if (!playlist) return;
    deletePlaylist.mutate(playlist.playlist_id, {
      onSuccess: () => {
        toast("Playlist deleted.", "success");
        navigate("/library");
      },
      onError: () => toast("Failed to delete playlist.", "error"),
    });
  };

  if (!userId) {
    return (
      <div>
        <PageHeader title="Playlist" description="" />
        <GlassCard>
          <p className="text-sm text-dark-400">Enter a user ID on the Library page first.</p>
        </GlassCard>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Playlist" description="" />
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div>
        <PageHeader title="Playlist" description="" />
        <GlassCard>
          <p className="text-sm text-dark-400">Playlist not found.</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate("/library")}
          className="rounded-[11px] p-1.5 text-dark-300 hover:bg-dark-600 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <PageHeader title={playlist.name} description={playlist.description || `${playlist.track_count} tracks`} />
      </div>

      <div className="mb-4 flex gap-2">
        <Button
          variant="danger"
          size="sm"
          onClick={handleDeletePlaylist}
          disabled={deletePlaylist.isPending}
        >
          Delete Playlist
        </Button>
      </div>

      {playlist.tracks.length === 0 ? (
        <GlassCard>
          <div className="flex flex-col items-center gap-2 py-8">
            <Music className="h-8 w-8 text-dark-500" />
            <p className="text-sm text-dark-400">This playlist is empty</p>
          </div>
        </GlassCard>
      ) : (
        <div className="glass rounded-xl p-4">
          <div className="space-y-1">
            {playlist.tracks.map((track) => (
              <div
                key={`${track.identifier}-${track.position}`}
                className="group flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-dark-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 text-center text-xs font-bold text-dark-400">
                    {track.position + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="truncate text-dark-100">{track.title}</div>
                    <div className="truncate text-xs text-dark-400">{track.author}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-dark-400">{fmtMs(track.length)}</span>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handlePlay(track.uri)}
                      className="rounded p-1 text-dark-400 hover:text-accent-violet transition-colors"
                      title="Play"
                    >
                      <Play className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleRemoveTrack(track.position)}
                      disabled={removeTrack.isPending}
                      className="rounded p-1 text-dark-400 hover:text-accent-red transition-colors"
                      title="Remove"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
