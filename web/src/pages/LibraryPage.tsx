import { useState } from "react";
import { useAuthStore } from "../hooks/use-auth-store";
import PageHeader from "../components/shared/PageHeader";
import Input from "../components/ui/Input";
import FavoritesList from "../features/library/FavoritesList";
import PlaylistsList from "../features/library/PlaylistsList";

export default function LibraryPage() {
  const { userId, setUserId } = useAuthStore();
  const [localUserId, setLocalUserId] = useState(userId);

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
          <PlaylistsList userId={userId} />
        </div>
      )}
    </div>
  );
}
