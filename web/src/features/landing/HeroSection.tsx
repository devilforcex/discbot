import { Link } from "react-router-dom";
import { ExternalLink } from "lucide-react";

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden px-6 pt-32 pb-20 md:pt-48 md:pb-28">
      {/* Background grid */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-50" />
      {/* Background radial */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-radial" />

      <div className="relative z-10 mx-auto max-w-7xl text-center">
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-accent-violet/30 bg-accent-violet/10 px-3 py-1 text-xs font-medium text-accent-violet">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-violet opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-violet" />
          </span>
          DrusaBota — Made with ❤️ by Steel
        </div>

        <h1 className="mb-6 text-5xl font-bold tracking-tight text-white md:text-7xl lg:text-8xl font-[family-name:var(--font-heading)] text-shadow-heading">
          Music that feels
          <br />
          <span className="text-gradient">native to Discord.</span>
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-lg font-light leading-relaxed text-dark-300 md:text-xl">
          Lavalink v4 audio, prefix commands, whitelist access control, playlists
          &amp; favorites — plus a solid dark dashboard and embed player with
          real buttons.
        </p>

        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href="https://github.com/devilforcex/discbot"
            target="_blank"
            rel="noreferrer"
            className="group flex w-full items-center justify-center gap-2 rounded-[11px] bg-accent-violet px-8 py-3.5 text-sm font-semibold text-white transition-all hover:bg-accent-violet/80 hover:scale-105 active:scale-95 sm:w-auto shadow-[0_0_16px_rgba(104,31,209,0.35)]"
          >
            View on GitHub
            <ExternalLink className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </a>
          <Link
            to="/dashboard"
            className="flex w-full items-center justify-center rounded-[11px] border border-dark-500 bg-dark-700 px-8 py-3.5 text-sm font-medium text-dark-200 transition-all hover:text-white hover:border-dark-400 sm:w-auto"
          >
            Open Dashboard
          </Link>
        </div>

        {/* Banner */}
        <div className="relative mx-auto mt-12 max-w-4xl">
          <img
            src="/assets/steel-music-bot-logo.png"
            alt="Steel Music Bot Banner"
            className="w-full rounded-2xl border border-dark-500 shadow-[0_0_40px_rgba(104,31,209,0.15)]"
          />
          <p className="mt-3 text-xs text-dark-400">
            Official banner — DrusaBota • Steel Music Bot
          </p>
        </div>

        {/* Abstract dashboard mock */}
        <div className="relative mx-auto mt-20 max-w-5xl">
          <div className="absolute inset-0 z-10 pointer-events-none bg-gradient-to-t from-dark-900 via-transparent to-transparent" />
          <div className="glass rounded-xl p-2 md:p-4">
            <div className="relative aspect-[16/9] overflow-hidden rounded-lg border border-dark-500 bg-dark-800">
              <div className="absolute inset-0 flex">
                {/* Sidebar mock */}
                <div className="hidden w-48 border-r border-dark-500 p-4 md:block">
                  <div className="mb-6 flex items-center gap-2">
                    <div className="h-7 w-7 rounded-[11px] bg-gradient-to-br from-accent-violet to-accent-fuchsia" />
                    <div className="h-3 w-20 rounded bg-dark-500/60" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-8 rounded-[11px] border border-accent-violet/25 bg-accent-violet/15" />
                    <div className="h-8 rounded-[11px] bg-dark-600/40" />
                    <div className="h-8 rounded-[11px] bg-dark-600/40" />
                    <div className="h-8 rounded-[11px] bg-dark-600/40" />
                  </div>
                </div>
                {/* Content mock */}
                <div className="flex flex-1 flex-col gap-4 p-4 md:p-8">
                  <div className="flex items-center justify-between">
                    <div className="h-6 w-36 rounded bg-dark-600/50" />
                    <div className="flex items-center gap-2 text-xs text-accent-emerald">
                      <span className="h-2 w-2 rounded-full bg-accent-emerald" /> Online
                    </div>
                  </div>
                  <div className="glass flex items-center gap-4 rounded-xl border border-accent-violet/20 p-4">
                    <div className="h-16 w-16 flex-shrink-0 rounded-lg border border-accent-violet/30 bg-accent-violet/20" />
                    <div className="min-w-0 flex-1">
                      <div className="mb-2 h-4 w-2/3 rounded bg-dark-500/70" />
                      <div className="mb-3 h-3 w-1/3 rounded bg-dark-600/70" />
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-dark-600">
                        <div className="h-full w-2/5 rounded-full bg-gradient-to-r from-accent-violet to-accent-fuchsia" />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="glass h-20 rounded-xl border border-dark-500" />
                    <div className="glass h-20 rounded-xl border border-dark-500" />
                    <div className="glass h-20 rounded-xl border border-dark-500" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
