import { useState } from "react";
import { X, Eye, EyeOff, LogIn } from "lucide-react";
import { useAuthStore } from "../../hooks/use-auth-store";

interface ConnectModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function ConnectModal({ open, onClose, onSuccess }: ConnectModalProps) {
  const [token, setToken] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const setTokenStore = useAuthStore((s) => s.setToken);

  if (!open) return null;

  const handleConnect = () => {
    const trimmed = token.trim();
    if (!trimmed) {
      setError("Token is required");
      return;
    }
    setTokenStore(trimmed);
    setError("");
    onSuccess?.();
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleConnect();
    if (e.key === "Escape") onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="glass relative mx-4 w-full max-w-md rounded-2xl border border-dark-500 p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-dark-400 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-[11px] bg-accent-violet/20">
            <LogIn className="h-5 w-5 text-accent-violet" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Connect to Bot</h2>
            <p className="text-xs text-dark-400">Enter the dashboard secret key</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-dark-300">Secret Key</label>
            <div className="relative">
              <input
                type={show ? "text" : "password"}
                value={token}
                onChange={(e) => { setToken(e.target.value); setError(""); }}
                onKeyDown={handleKeyDown}
                placeholder="Paste your DASHBOARD_SECRET_KEY"
                className="w-full rounded-[11px] border border-dark-500 bg-dark-700 px-3 py-2.5 pr-10 text-sm text-white placeholder:text-dark-500 focus:border-accent-violet/50 focus:outline-none focus:ring-1 focus:ring-accent-violet/30"
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShow(!show)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white transition-colors"
              >
                {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {error && <p className="mt-1 text-xs text-accent-red">{error}</p>}
          </div>

          <button
            onClick={handleConnect}
            className="w-full rounded-[11px] bg-accent-violet py-2.5 text-sm font-semibold text-white transition-all hover:bg-accent-violet/80 hover:scale-[1.02] active:scale-95 shadow-[0_0_16px_rgba(104,31,209,0.35)]"
          >
            Connect
          </button>
        </div>

        <p className="mt-4 text-center text-[11px] text-dark-500">
          Ask the bot operator for the secret key configured in{" "}
          <code className="rounded bg-dark-800 px-1 py-0.5">DASHBOARD_SECRET_KEY</code>
        </p>
      </div>
    </div>
  );
}
