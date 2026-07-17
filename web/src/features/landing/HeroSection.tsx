import { useAuthStore } from "../../hooks/use-auth-store";
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import ConnectModal from "../../components/shared/ConnectModal";

export default function HeroSection() {
  const token = useAuthStore((s) => s.token);
  const [searchParams, setSearchParams] = useSearchParams();
  const [connectOpen, setConnectOpen] = useState(false);

  useEffect(() => {
    if (searchParams.get("connect") === "1") {
      setConnectOpen(true);
      searchParams.delete("connect");
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const handleConnectSuccess = () => {
    window.location.href = "/dashboard";
  };

  return (
    <>
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-24 sm:mt-32 mb-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-20 items-center">
          {/* Left column - text */}
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-[11px] bg-gradient-to-br from-accent-blue-600 to-accent-blue-300 flex items-center justify-center">
                <span className="text-white font-black text-sm">DB</span>
              </div>
              <span className="text-3xl font-bold tracking-tight text-white">DrusaBoT</span>
            </div>
            <p className="text-[11px] sm:text-xs font-bold tracking-[0.25em] uppercase bg-gradient-to-r from-accent-blue-600 via-accent-blue to-accent-blue-300 bg-clip-text text-transparent mb-10">
              Next-Level Music Experience
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-[-0.02em] text-white mb-5">
              What is DrusaBoT?
            </h2>
            <p className="text-dark-300 text-base leading-relaxed max-w-[520px] mb-7">
              High-quality Discord music bot powered by Lavalink v4. Stream from YouTube,
              Spotify & more with low-latency audio, queue management, audio filters,
              playlists and a real-time web dashboard.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setConnectOpen(true)}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-[11px] font-bold bg-gradient-to-r from-accent-blue-600 via-accent-blue to-accent-blue-300 text-white shadow-[0_8px_30px_rgba(28,126,239,0.45)] hover:shadow-[0_12px_40px_rgba(74,159,255,0.6)] hover:scale-[1.03] transition-all duration-200 whitespace-nowrap"
              >
                {token ? "Open Dashboard" : "Connect to Dashboard"}
              </button>
              <a
                href="https://github.com/devilforcex/DrusaBoT"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-[11px] font-semibold border border-dark-500 text-dark-200 hover:text-white hover:border-accent-blue/40 transition-colors whitespace-nowrap"
              >
                View on GitHub
              </a>
            </div>
          </div>

          {/* Right column - mockups */}
          <div className="relative h-[460px] sm:h-[500px] flex items-center justify-center lg:justify-end group/stage">
            <div className="absolute inset-0 -z-10 flex items-center justify-center">
              <div className="h-[360px] w-[360px] rounded-full bg-accent-blue-600/18 blur-[110px]" />
            </div>
            <div className="absolute -z-10 left-1/4 top-4 h-[200px] w-[200px] rounded-full bg-accent-blue/18 blur-[90px]" aria-hidden="true" />
            <div className="absolute -z-10 right-0 bottom-0 h-[220px] w-[220px] rounded-full bg-accent-blue-300/10 blur-[80px]" aria-hidden="true" />
            <div
              className="absolute inset-0 -z-10 opacity-[0.09]"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(74,159,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(74,159,255,0.5) 1px, transparent 1px)",
                backgroundSize: "48px 48px",
                maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
                WebkitMaskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
              }}
              aria-hidden="true"
            />

            {/* Discord voice channel mockup */}
            <div className="absolute left-0 sm:left-2 bottom-4 z-10 rotate-[-5deg] group-hover/stage:rotate-[-3deg] group-hover/stage:-translate-y-1 transition-all duration-500">
              <div className="rounded-2xl border border-dark-500 bg-dark-700 shadow-[0_25px_70px_-20px_rgba(0,0,0,0.85)] overflow-hidden w-[240px] sm:w-[260px]">
                <div className="flex items-center justify-between px-3 py-2.5 border-b border-dark-500 bg-gradient-to-b from-dark-800 to-dark-700">
                  <div className="flex items-center gap-1.5">
                    <div className="w-4 h-4 rounded-sm bg-gradient-to-br from-accent-blue-600 to-accent-blue flex items-center justify-center">
                      <span className="text-white font-black text-[8px]">DB</span>
                    </div>
                    <span className="text-[11px] font-bold text-white">Music Central</span>
                  </div>
                  <span className="text-[8px] font-bold px-1.5 py-0.5 rounded bg-accent-emerald/15 text-accent-emerald">ONLINE</span>
                </div>
                <div className="px-2 pt-2 pb-1">
                  <div className="flex items-center gap-1.5 px-2 py-1 text-dark-300">
                    <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" x2="20" y1="9" y2="9" /><line x1="4" x2="20" y1="15" y2="15" /><line x1="10" x2="8" y1="3" y2="21" /><line x1="16" x2="14" y1="3" y2="21" /></svg>
                    <span className="text-[10px]">music-chat</span>
                  </div>
                </div>
                <div className="px-2 pb-3">
                  <div className="mb-1">
                    <div className="flex items-center gap-1.5 px-2 py-1 text-dark-300">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" /><path d="M16 9a5 5 0 0 1 0 6" /></svg>
                      <span className="text-[11px]">Main Stage</span>
                      <span className="text-[8px] text-dark-400 ml-auto">1</span>
                    </div>
                    <div className="flex items-center gap-2 pl-5 py-1.5 rounded-md bg-accent-blue/5">
                      <div className="relative flex-shrink-0">
                        <div className="bg-dark-500 p-0.5 rounded ring-1 ring-accent-blue/40">
                          <div className="w-[14px] h-[14px] rounded-sm bg-gradient-to-br from-accent-blue-600 to-accent-blue-300 flex items-center justify-center">
                            <span className="text-white font-black text-[6px]">DB</span>
                          </div>
                        </div>
                        <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-accent-emerald border border-dark-700" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <p className="text-[11px] font-semibold leading-tight text-white">DrusaBoT</p>
                          <div className="flex items-end gap-[2px] h-2.5 ml-auto">
                            <span className="w-[2px] rounded-full bg-accent-emerald animate-bar1" />
                            <span className="w-[2px] rounded-full bg-accent-emerald animate-bar2" />
                            <span className="w-[2px] rounded-full bg-accent-emerald animate-bar3" />
                          </div>
                        </div>
                        <p className="text-[9px] text-dark-400 truncate">Playing a chill track</p>
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 px-2 py-1 text-dark-300">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" /><path d="M16 9a5 5 0 0 1 0 6" /></svg>
                      <span className="text-[11px]">Chill Lounge</span>
                      <span className="text-[8px] ml-auto">1</span>
                    </div>
                    <div className="flex items-center gap-2 pl-5 py-1.5 rounded-md">
                      <div className="relative flex-shrink-0">
                        <div className="bg-dark-500 p-0.5 rounded">
                          <div className="w-[14px] h-[14px] rounded-sm bg-gradient-to-br from-accent-blue-600 to-accent-blue-300 flex items-center justify-center">
                            <span className="text-white font-black text-[6px]">DB</span>
                          </div>
                        </div>
                        <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-dark-400 border border-dark-700" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-semibold leading-tight text-dark-100">DrusaBoT</p>
                        <p className="text-[9px] text-dark-400 truncate">Ready to play</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Control panel mockup */}
            <div className="absolute right-0 sm:right-2 top-0 z-20 rotate-[3deg] group-hover/stage:rotate-[1deg] group-hover/stage:-translate-y-1 transition-all duration-500">
              <div className="rounded-2xl border border-dark-500 bg-gradient-to-br from-dark-700 to-dark-800 shadow-[0_30px_80px_-25px_rgba(0,0,0,0.9),_0_0_0_1px_rgba(74,159,255,0.06)] w-[340px] sm:w-[380px] overflow-hidden">
                <div className="h-0.5 bg-gradient-to-r from-transparent via-accent-blue to-transparent" />
                <div className="flex items-center justify-between px-4 py-3 border-b border-dark-500">
                  <div className="flex items-center gap-2">
                    <div className="w-[22px] h-[22px] rounded bg-gradient-to-br from-accent-blue-600 to-accent-blue-300 flex items-center justify-center">
                      <span className="text-white font-black text-[9px]">DB</span>
                    </div>
                    <span className="text-sm font-bold text-white">DrusaBoT</span>
                    <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-accent-emerald/15 text-accent-emerald font-bold">
                      <span className="w-1 h-1 rounded-full bg-accent-emerald animate-pulse" />
                      LIVE
                    </span>
                  </div>
                  <p className="text-[10px] font-bold tracking-[0.3em] bg-gradient-to-r from-accent-blue-600 via-accent-blue to-accent-blue-300 bg-clip-text text-transparent">
                    CONTROL PANEL
                  </p>
                </div>
                <div className="px-4 py-3 border-b border-dark-500">
                  <div className="flex items-center gap-3">
                    <div className="relative w-11 h-11 rounded-[11px] overflow-hidden flex-shrink-0 shadow-[0_4px_14px_rgba(28,126,239,0.4)] ring-1 ring-accent-blue/30 bg-gradient-to-br from-accent-blue-600/30 to-accent-blue-300/30 flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" /></svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-bold text-white truncate">Midnight Dreams</p>
                      <p className="text-[10px] text-dark-400 truncate">Artist Name</p>
                      <div className="mt-1.5 flex items-center gap-1.5">
                        <span className="text-[9px] font-mono text-dark-400">1:24</span>
                        <div className="relative h-1 flex-1 rounded-full bg-dark-500 overflow-hidden">
                          <div className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-accent-blue-600 to-accent-blue-300 w-[42%]">
                            <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-2 h-2 rounded-full bg-white shadow-[0_0_8px_#7fbaff]" />
                          </div>
                        </div>
                        <span className="text-[9px] font-mono text-dark-400">3:31</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-4 grid grid-cols-5 gap-2">
                  {[
                    { active: true, icon: "play" },
                    { active: false, icon: "skip-back" },
                    { active: true, icon: "pause" },
                    { active: false, icon: "skip-forward" },
                    { active: true, icon: "list-music" },
                    { active: true, icon: "repeat" },
                    { active: false, icon: "rewind" },
                    { active: false, icon: "heart", color: "text-red-500 fill-red-500" },
                    { active: false, icon: "fast-forward" },
                    { active: true, icon: "volume-2" },
                    { active: true, icon: "list-video" },
                    { active: false, icon: "shuffle" },
                    { active: true, icon: "disc-3" },
                    { active: false, icon: "filter" },
                    { active: true, icon: "circle-help" },
                  ].map((btn, i) => (
                    <div
                      key={i}
                      className={`aspect-square rounded-lg flex items-center justify-center transition-colors ${
                        btn.active
                          ? "bg-accent-blue/15 text-accent-blue ring-1 ring-accent-blue/30 hover:bg-accent-blue/25"
                          : "bg-dark-600 text-dark-100 ring-1 ring-dark-500 hover:bg-dark-500"
                      } ${btn.color || ""}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={btn.icon === "heart" ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide">
                        {btn.icon === "play" && <polygon points="6 3 20 12 6 21 6 3" />}
                        {btn.icon === "skip-back" && <><polygon points="19 20 9 12 19 4 19 20" /><line x1="5" x2="5" y1="19" y2="5" /></>}
                        {btn.icon === "pause" && <><rect x="14" y="4" width="4" height="16" rx="1" /><rect x="6" y="4" width="4" height="16" rx="1" /></>}
                        {btn.icon === "skip-forward" && <><polygon points="5 4 15 12 5 20 5 4" /><line x1="19" x2="19" y1="5" y2="19" /></>}
                        {btn.icon === "list-music" && <><path d="M21 15V6" /><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" /><path d="M12 12H3" /><path d="M16 6H3" /><path d="M12 18H3" /></>}
                        {btn.icon === "repeat" && <><path d="m17 2 4 4-4 4" /><path d="M3 11v-1a4 4 0 0 1 4-4h14" /><path d="m7 22-4-4 4-4" /><path d="M21 13v1a4 4 0 0 1-4 4H3" /></>}
                        {btn.icon === "rewind" && <><polygon points="11 19 2 12 11 5 11 19" /><polygon points="22 19 13 12 22 5 22 19" /></>}
                        {btn.icon === "heart" && <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />}
                        {btn.icon === "fast-forward" && <><polygon points="13 19 22 12 13 5 13 19" /><polygon points="2 19 11 12 2 5 2 19" /></>}
                        {btn.icon === "volume-2" && <><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" /><path d="M16 9a5 5 0 0 1 0 6" /><path d="M19.364 18.364a9 9 0 0 0 0-12.728" /></>}
                        {btn.icon === "list-video" && <><path d="M12 12H3" /><path d="M16 6H3" /><path d="M12 18H3" /><path d="m16 12 5 3-5 3v-6Z" /></>}
                        {btn.icon === "shuffle" && <><path d="m18 14 4 4-4 4" /><path d="m18 2 4 4-4 4" /><path d="M2 18h1.973a4 4 0 0 0 3.3-1.7l5.454-8.6a4 4 0 0 1 3.3-1.7H22" /><path d="M2 6h1.972a4 4 0 0 1 3.6 2.2" /><path d="M22 18h-6.041a4 4 0 0 1-3.3-1.8l-.359-.45" /></>}
                        {btn.icon === "disc-3" && <><circle cx="12" cy="12" r="10" /><path d="M6 12c0-1.7.7-3.2 1.8-4.2" /><circle cx="12" cy="12" r="2" /><path d="M18 12c0 1.7-.7 3.2-1.8 4.2" /></>}
                        {btn.icon === "filter" && <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />}
                        {btn.icon === "circle-help" && <><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><path d="M12 17h.01" /></>}
                      </svg>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Floating dots */}
            <div className="absolute top-8 right-[30%] z-30 w-1.5 h-1.5 rounded-full bg-accent-blue-300 shadow-[0_0_12px_#4a9fff]" />
            <div className="absolute bottom-14 right-[55%] z-30 w-2 h-2 rounded-full bg-accent-blue shadow-[0_0_18px_#1c7eef]" />
            <div className="absolute top-[45%] left-[8%] z-30 w-1 h-1 rounded-full bg-[#c2dcff] shadow-[0_0_10px_#7fbaff]" />
            <div className="absolute top-[15%] left-[40%] z-30 w-1 h-1 rounded-full bg-accent-blue/70 shadow-[0_0_8px_#4a9fff]" />
            <div className="absolute bottom-6 right-[10%] z-30 w-1.5 h-1.5 rounded-full bg-accent-blue-300/80 shadow-[0_0_14px_#4a9fff]" />
          </div>
        </div>
      </section>

      <ConnectModal
        open={connectOpen}
        onClose={() => setConnectOpen(false)}
        onSuccess={handleConnectSuccess}
      />
    </>
  );
}