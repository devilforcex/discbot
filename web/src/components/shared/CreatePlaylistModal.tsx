import { useState } from "react";
import { X, ListPlus } from "lucide-react";
import { useCreatePlaylist } from "../../hooks/use-playlists";
import { useToast } from "../ui/Toast";

interface CreatePlaylistModalProps {
  userId: string;
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function CreatePlaylistModal({ userId, open, onClose, onSuccess }: CreatePlaylistModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const createPlaylist = useCreatePlaylist(userId);
  const { toast } = useToast();

  if (!open) return null;

  const handleCreate = () => {
    const trimmed = name.trim();
    if (!trimmed) {
      toast("Playlist name is required.", "error");
      return;
    }
    createPlaylist.mutate(
      { name: trimmed, description: description.trim() },
      {
        onSuccess: () => {
          toast("Playlist created!", "success");
          setName("");
          setDescription("");
          onSuccess?.();
          onClose();
        },
        onError: (err) => {
          toast(err.message || "Failed to create playlist.", "error");
        },
      },
    );
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="glass relative mx-4 w-full max-w-md rounded-2xl border border-white/10 p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-dark-400 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-violet/20">
            <ListPlus className="h-5 w-5 text-accent-violet" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Create Playlist</h2>
            <p className="text-xs text-dark-400">Add a new playlist to your library</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-dark-300">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              placeholder="My Playlist"
              className="w-full rounded-lg border border-white/10 bg-dark-800/50 px-3 py-2.5 text-sm text-white placeholder:text-dark-500 focus:border-accent-violet/50 focus:outline-none focus:ring-1 focus:ring-accent-violet/30"
              autoFocus
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-dark-300">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="A short description..."
              rows={2}
              className="w-full rounded-lg border border-white/10 bg-dark-800/50 px-3 py-2.5 text-sm text-white placeholder:text-dark-500 focus:border-accent-violet/50 focus:outline-none focus:ring-1 focus:ring-accent-violet/30 resize-none"
            />
          </div>

          <button
            onClick={handleCreate}
            disabled={createPlaylist.isPending}
            className="w-full rounded-lg bg-accent-violet py-2.5 text-sm font-semibold text-white transition-all hover:bg-accent-violet/80 hover:scale-[1.02] active:scale-95 disabled:opacity-50"
          >
            {createPlaylist.isPending ? "Creating..." : "Create Playlist"}
          </button>
        </div>
      </div>
    </div>
  );
}
