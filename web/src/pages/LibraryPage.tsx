import { useState } from "react";
import { useAuthStore } from "../hooks/use-auth-store";
import PageHeader from "../components/shared/PageHeader";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import FavoritesList from "../features/library/FavoritesList";
import PlaylistsList from "../features/library/PlaylistsList";
import CreatePlaylistModal from "../components/shared/CreatePlaylistModal";
import { Plus } from "lucide-react";

export default function LibraryPage() {
  const { userId, setUserId } = useAuthStore();
  const [localUserId, setLocalUserId] = useState(userId);
  const [createOpen, setCreateOpen] = useState(false);

  const handleApply = () => {
    setUserId(localUserId);
  };

  return (
    <div>
      <PageHeader title="Library" description="Favorites and playlists" />
      <div className="mb-6 flex items-end gap-3">
        <Input
          label="Discord User ID"
          placeholder="Enter user ID..."
          value={localUserId}
          onChange={(e) => setLocalUserId(e.target.value)}
          className="max-w-xs"
        />
        <button
          onClick={handleApply}
          className="rounded-lg bg-accent-violet px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-violet/80"
        >
          Load
        </button>
      </div>
      {userId && (
        <div className="space-y-6">
          <FavoritesList userId={userId} />
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-dark-100">Playlists</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCreateOpen(true)}
              >
                <Plus className="h-3.5 w-3.5 mr-1" />
                New Playlist
              </Button>
            </div>
            <PlaylistsList userId={userId} />
          </div>
        </div>
      )}
      <CreatePlaylistModal
        userId={userId}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
    </div>
  );
}
