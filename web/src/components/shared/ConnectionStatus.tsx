import { useWs, type WsStatus } from "../../hooks/use-ws";

const statusStyles: Record<WsStatus, { dot: string; label: string }> = {
  connected: { dot: "bg-emerald-400", label: "Live" },
  connecting: { dot: "bg-amber-400 animate-pulse", label: "Connecting" },
  disconnected: { dot: "bg-dark-500", label: "Offline" },
};

export default function ConnectionStatus() {
  const status = useWs();
  const { dot, label } = statusStyles[status];

  return (
    <div className="flex items-center gap-1.5" title={`WebSocket: ${label}`}>
      <div className={`h-2 w-2 rounded-full ${dot}`} />
      <span className="hidden text-xs text-dark-400 sm:inline">{label}</span>
    </div>
  );
}
