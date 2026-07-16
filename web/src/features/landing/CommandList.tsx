import { useState } from "react";
import { Search } from "lucide-react";

interface Command {
  cmd: string;
  name: string;
  desc: string;
  cat: "music" | "admin" | "utility";
}

const COMMANDS: Command[] = [
  { cmd: "!play", name: "Play Music", desc: "Search YouTube/Spotify or play from URL.", cat: "music" },
  { cmd: "!pause", name: "Pause", desc: "Pause current playback.", cat: "music" },
  { cmd: "!resume", name: "Resume", desc: "Resume paused playback.", cat: "music" },
  { cmd: "!skip", name: "Skip", desc: "Skip to the next track.", cat: "music" },
  { cmd: "!stop", name: "Stop", desc: "Stop playback and clear queue.", cat: "music" },
  { cmd: "!queue", name: "Queue", desc: "View the current queue.", cat: "music" },
  { cmd: "!nowplaying", name: "Now Playing", desc: "Show track + player buttons.", cat: "music" },
  { cmd: "!volume", name: "Volume", desc: "Set volume 0–100.", cat: "music" },
  { cmd: "!loop", name: "Loop", desc: "Loop mode: none | track | queue.", cat: "music" },
  { cmd: "!shuffle", name: "Shuffle", desc: "Shuffle the queue.", cat: "music" },
  { cmd: "!favorite", name: "Favorite", desc: "Save current track.", cat: "music" },
  { cmd: "!filter", name: "Audio Filter", desc: "Bassboost, Nightcore, Vaporwave, Pop, 8D etc.", cat: "music" },
  { cmd: "!filters", name: "Filters List", desc: "Interactive filter select menu.", cat: "music" },
  { cmd: "!seek", name: "Seek", desc: "Seek forward/backward + replay.", cat: "music" },
  { cmd: "!adduser", name: "Add User", desc: "Whitelist a user (owner).", cat: "admin" },
  { cmd: "!blacklist", name: "Blacklist", desc: "Block a user (owner).", cat: "admin" },
  { cmd: "!247", name: "24/7 Mode", desc: "Toggle always-on voice (owner).", cat: "admin" },
  { cmd: "!requestaccess", name: "Request Access", desc: "Ask owner for whitelist.", cat: "utility" },
  { cmd: "!status", name: "Status", desc: "Bot uptime, Lavalink, queue.", cat: "utility" },
  { cmd: "!whoami", name: "Who Am I", desc: "Your ID and access status.", cat: "utility" },
  { cmd: "!help", name: "Help", desc: "Interactive help with categories dropdown.", cat: "utility" },
];

const catColors: Record<string, string> = {
  music: "text-accent-violet bg-accent-violet/10",
  admin: "text-accent-fuchsia bg-accent-fuchsia/10",
  utility: "text-accent-blue bg-accent-blue/10",
};

const filters: { key: string; label: string }[] = [
  { key: "all", label: "All" },
  { key: "music", label: "Music" },
  { key: "admin", label: "Admin" },
  { key: "utility", label: "Utility" },
];

export default function CommandList() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  const filtered = COMMANDS.filter(
    (c) =>
      (activeFilter === "all" || c.cat === activeFilter) &&
      (!search ||
        (c.cmd + c.name + c.desc).toLowerCase().includes(search.toLowerCase())),
  );

  return (
    <section id="commands" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-white md:text-4xl font-[family-name:var(--font-heading)]">
            Commands
          </h2>
          <p className="text-dark-300">
            Prefix <span className="font-mono text-accent-violet">!</span> —
            full list also via{" "}
            <span className="font-mono text-accent-violet">!help</span>.
          </p>
        </div>
        <div className="overflow-hidden rounded-2xl border border-dark-500 glass">
          {/* Search & filters */}
          <div className="border-b border-dark-500 bg-dark-800/50 p-6">
            <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
              <div className="relative w-full md:w-96">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
                <input
                  type="text"
                  placeholder="Search commands..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full rounded-[11px] border border-dark-500 bg-dark-900 py-2.5 pl-10 pr-4 text-sm text-dark-200 placeholder-dark-500 focus:border-accent-violet/50 focus:outline-none transition-colors"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {filters.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setActiveFilter(f.key)}
                    className={`rounded-full px-4 py-1.5 text-xs font-medium border transition-colors ${
                      activeFilter === f.key
                        ? "bg-accent-violet/10 text-accent-violet border-accent-violet/20"
                        : "bg-dark-700/50 text-dark-300 border-dark-500 hover:text-white"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {/* Command list */}
          <div className="divide-y divide-dark-500">
            {filtered.map((c) => (
              <div
                key={c.cmd}
                className="flex flex-col justify-between gap-4 p-4 transition-colors hover:bg-dark-600/50 md:flex-row md:items-center"
              >
                <div className="flex items-start gap-4">
                  <span
                    className={`mt-1 rounded px-2 py-1 font-mono text-xs ${catColors[c.cat]}`}
                  >
                    {c.cmd}
                  </span>
                  <div>
                    <h4 className="text-sm font-medium text-white">{c.name}</h4>
                    <p className="mt-1 text-xs text-dark-400">{c.desc}</p>
                  </div>
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider text-dark-500">
                  {c.cat}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
