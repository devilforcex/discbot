import GlassCard from "../../components/ui/GlassCard";

const endpoints = [
  { method: "GET", path: "/api/health", desc: "Health check" },
  { method: "GET", path: "/api/status", desc: "Bot status" },
  { method: "GET", path: "/api/guilds", desc: "Guild list" },
  { method: "GET", path: "/api/lavalink", desc: "Lavalink status" },
  { method: "GET", path: "/api/overview/{guild_id}", desc: "Full overview" },
];

export default function QuickApiLinks() {
  return (
    <GlassCard className="mt-6">
      <h3 className="mb-3 text-sm font-medium text-dark-100">API Endpoints</h3>
      <div className="space-y-2">
        {endpoints.map((ep) => (
          <div key={ep.path} className="flex items-center gap-3 text-sm">
            <span className="w-12 rounded bg-accent-emerald/15 px-1.5 py-0.5 text-center text-xs font-medium text-accent-emerald">
              {ep.method}
            </span>
            <code className="font-mono text-dark-200">{ep.path}</code>
            <span className="text-dark-400">— {ep.desc}</span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}
