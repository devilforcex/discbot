export default function PlayerPreview() {
  return (
    <section id="player" className="border-y border-white/5 bg-dark-800/20 px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-medium tracking-tight text-white md:text-4xl">
            Discord embed player
          </h2>
          <p className="text-dark-300">
            What users see in the music channel — buttons that actually control
            playback.
          </p>
        </div>
        <div className="overflow-hidden rounded-2xl border border-white/10 glass">
          {/* Header */}
          <div className="flex items-center gap-2 border-b border-white/5 p-6">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-accent-violet to-accent-fuchsia" />
            <div>
              <div className="text-sm font-medium text-white">Nightmare Music</div>
              <div className="text-[10px] uppercase tracking-wider text-dark-400">
                APP · BOT
              </div>
            </div>
          </div>
          {/* Player embed */}
          <div className="p-6">
            <div className="rounded-xl border-l-4 border-accent-violet bg-dark-800/60 p-5">
              <div className="mb-1 text-xs text-dark-400">🎵 Now Playing</div>
              <div className="mb-1 font-medium text-white">Blinding Lights</div>
              <div className="mb-4 text-sm text-dark-300">The Weeknd</div>
              <div className="mb-1 font-mono text-xs text-dark-400">
                ▓▓▓▓▓▓▓░░░░░░░░░ 1:42 / 3:20
              </div>
              <div className="mb-4 text-xs text-dark-400">
                🔊 65% · 🔁 Queue · 🤖 Autoplay · Requested by @you
              </div>
              <div className="flex flex-wrap gap-2">
                {["⏯", "⏭", "⏹", "🔀", "🔁", "🔉", "🔊", "⭐", "📋"].map(
                  (emoji, i) => (
                    <span
                      key={i}
                      className="flex h-9 w-10 items-center justify-center rounded-md bg-dark-600 text-sm text-white"
                    >
                      {emoji}
                    </span>
                  ),
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
