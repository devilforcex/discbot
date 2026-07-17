export default function SupportedSources() {
  const sources = [
    { name: "Spotify", color: "#1DB954" },
    { name: "YouTube", color: "#FF0000" },
    { name: "Apple Music", color: "#FA243C" },
    { name: "SoundCloud", color: "#FF7700" },
    { name: "Deezer", color: "#A238FF" },
    { name: "Tidal", color: "#000000" },
  ];

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mb-24">
      <div className="mb-8 sm:mb-10">
        <p className="text-[11px] sm:text-xs font-bold tracking-[0.25em] uppercase bg-gradient-to-r from-accent-blue-600 via-accent-blue to-accent-blue-300 bg-clip-text text-transparent mb-3">
          Supported Sources
        </p>
        <h2 className="text-3xl sm:text-4xl font-bold tracking-[-0.02em] text-white mb-3">
          World-class players, one bot
        </h2>
        <p className="text-dark-300 text-base leading-relaxed max-w-[520px]">
          Stream from the services you already love — DiscBot plays them all through
          Lavalink v4 audio node.
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {sources.map((source) => (
          <div
            key={source.name}
            className="group relative flex flex-col items-center justify-center gap-3 rounded-xl border border-dark-500 bg-dark-700/40 backdrop-blur-sm p-5 sm:p-6 transition-all duration-300 hover:-translate-y-1 hover:border-accent-blue/40 hover:bg-dark-700 hover:shadow-[0_15px_40px_-18px_rgba(74,159,255,0.5)]"
          >
            <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-accent-blue-600/[0.07] to-transparent pointer-events-none" />
            <div
              className="relative w-10 h-10 sm:w-11 sm:h-11 rounded-full flex items-center justify-center font-bold text-lg"
              style={{ backgroundColor: `${source.color}20`, color: source.color }}
            >
              {source.name.charAt(0)}
            </div>
            <p className="relative text-[13px] sm:text-sm font-semibold text-dark-100">
              {source.name}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}