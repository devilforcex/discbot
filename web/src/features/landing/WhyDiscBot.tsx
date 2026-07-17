const features = [
  { icon: "play", title: "Play Tracks", desc: "Play songs and playlists via links and names." },
  { icon: "skip-forward", title: "Skip", desc: "Skip current playing song and skip to." },
  { icon: "search", title: "Search", desc: "Modern tracks search results and prompts." },
  { icon: "list-music", title: "Queue", desc: "Advanced queue and now playing embed." },
  { icon: "fast-forward", title: "Seek", desc: "Seek forward, backward and custom duration." },
  { icon: "repeat", title: "Repeat", desc: "Repeat modes: track, queue and autoplay." },
  { icon: "shuffle", title: "Shuffle", desc: "Shuffle (re-order) the queue tracks." },
  { icon: "sliders-horizontal", title: "Filters", desc: "10+ different filters for audio effects." },
  { icon: "list-video", title: "Playlists", desc: "Create and manage custom playlists." },
  { icon: "mic", title: "DJ Role", desc: "Assign a specific role as music controller." },
  { icon: "history", title: "Track History", desc: "Replay previously played tracks." },
  { icon: "volume-2", title: "Volume", desc: "Adapt the audio volume to your liking." },
  { icon: "shield", title: "Access Control", desc: "Whitelist, blacklist, and permission system." },
  { icon: "clock", title: "24/7 Mode", desc: "Let the music stream non-stop in voice." },
  { icon: "radio", title: "Radio Mode", desc: "Non-stop radio in your voice channel." },
  { icon: "layers", title: "All-in-one", desc: "Everything you need in one bot." },
];

const iconSvg = (icon: string, className: string) => {
  const svgProps = { xmlns: "http://www.w3.org/2000/svg", width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" as const, strokeLinejoin: "round" as const, className };
  switch (icon) {
    case "play": return <svg {...svgProps}><polygon points="6 3 20 12 6 21 6 3" /></svg>;
    case "skip-forward": return <svg {...svgProps}><polygon points="5 4 15 12 5 20 5 4" /><line x1="19" x2="19" y1="5" y2="19" /></svg>;
    case "search": return <svg {...svgProps}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>;
    case "list-music": return <svg {...svgProps}><path d="M21 15V6" /><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" /><path d="M12 12H3" /><path d="M16 6H3" /><path d="M12 18H3" /></svg>;
    case "fast-forward": return <svg {...svgProps}><polygon points="13 19 22 12 13 5 13 19" /><polygon points="2 19 11 12 2 5 2 19" /></svg>;
    case "repeat": return <svg {...svgProps}><path d="m17 2 4 4-4 4" /><path d="M3 11v-1a4 4 0 0 1 4-4h14" /><path d="m7 22-4-4 4-4" /><path d="M21 13v1a4 4 0 0 1-4 4H3" /></svg>;
    case "shuffle": return <svg {...svgProps}><path d="m18 14 4 4-4 4" /><path d="m18 2 4 4-4 4" /><path d="M2 18h1.973a4 4 0 0 0 3.3-1.7l5.454-8.6a4 4 0 0 1 3.3-1.7H22" /><path d="M2 6h1.972a4 4 0 0 1 3.6 2.2" /><path d="M22 18h-6.041a4 4 0 0 1-3.3-1.8l-.359-.45" /></svg>;
    case "sliders-horizontal": return <svg {...svgProps}><line x1="21" x2="14" y1="4" y2="4" /><line x1="10" x2="3" y1="4" y2="4" /><line x1="21" x2="12" y1="12" y2="12" /><line x1="8" x2="3" y1="12" y2="12" /><line x1="21" x2="16" y1="20" y2="20" /><line x1="12" x2="3" y1="20" y2="20" /><line x1="14" x2="14" y1="2" y2="6" /><line x1="8" x2="8" y1="10" y2="14" /><line x1="16" x2="16" y1="18" y2="22" /></svg>;
    case "list-video": return <svg {...svgProps}><path d="M12 12H3" /><path d="M16 6H3" /><path d="M12 18H3" /><path d="m16 12 5 3-5 3v-6Z" /></svg>;
    case "mic": return <svg {...svgProps}><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" /></svg>;
    case "history": return <svg {...svgProps}><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l4 2" /></svg>;
    case "volume-2": return <svg {...svgProps}><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" /><path d="M16 9a5 5 0 0 1 0 6" /><path d="M19.364 18.364a9 9 0 0 0 0-12.728" /></svg>;
    case "shield": return <svg {...svgProps}><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" /></svg>;
    case "clock": return <svg {...svgProps}><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>;
    case "radio": return <svg {...svgProps}><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9" /><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5" /><circle cx="12" cy="12" r="2" /><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5" /><path d="M19.1 4.9C23 8.8 23 15.1 19.1 19" /></svg>;
    case "layers": return <svg {...svgProps}><path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z" /><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12" /><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17" /></svg>;
    default: return null;
  }
};

export default function WhyDiscBot() {
  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mb-24">
      <div className="mb-8 sm:mb-10">
        <h2 className="text-3xl sm:text-4xl font-bold tracking-[-0.02em] text-white mb-3">
          Why DiscBot?
        </h2>
        <p className="text-dark-300 text-base leading-relaxed">
          No paywalls, no votelocks.
          <br className="hidden sm:block" />
          <span className="bg-gradient-to-r from-accent-blue-600 via-accent-blue to-accent-blue-300 bg-clip-text text-transparent font-semibold">
            Listen to tracks with freedom!
          </span>
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        {features.map((feat) => (
          <div
            key={feat.title}
            className="group relative rounded-xl border border-dark-500 bg-dark-700/60 backdrop-blur-sm p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-accent-blue/40 hover:bg-dark-700 hover:shadow-[0_10px_30px_-15px_rgba(74,159,255,0.4)]"
          >
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-dark-800 border border-dark-500 mb-3 text-accent-blue group-hover:bg-accent-blue/10 transition-colors">
              {iconSvg(feat.icon, "")}
            </div>
            <h3 className="text-[13px] sm:text-sm font-bold text-white mb-1">{feat.title}</h3>
            <p className="text-[11px] sm:text-xs text-dark-400 leading-relaxed">{feat.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}