import { Code, MessageCircle } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-dark-900 px-6 pt-16 pb-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 md:flex-row md:justify-between">
        <div>
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-accent-violet to-accent-fuchsia text-[10px] font-bold text-white">
              DB
            </div>
            <span className="text-lg font-medium text-white">DrusaBota</span>
          </div>
          <p className="max-w-sm text-sm text-dark-400">
            Nightmare Music design language • Made with ❤️ by Steel • Private
            Discord music automation with filters &amp; interactive player.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <a
              href="https://discord.gg/jbjEpqwNn"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-accent-violet/30 bg-accent-violet/20 px-3 py-1.5 text-xs text-accent-violet transition-colors hover:bg-accent-violet/30"
            >
              <MessageCircle className="h-4 w-4" />
              Join Discord
            </a>
            <a
              href="https://github.com/devilforcex/discbot"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-dark-300 transition-colors hover:text-white"
            >
              <Code className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
        <div className="space-y-2 text-sm text-dark-400">
          <a href="https://github.com/devilforcex/discbot" className="block hover:text-accent-violet">GitHub</a>
          <a href="https://discord.gg/jbjEpqwNn" className="block hover:text-accent-violet">Discord Server</a>
          <a href="https://discord.com/developers/docs/bots/overview" className="block hover:text-accent-violet">Discord bot docs</a>
          <span className="block text-accent-violet/70">Made with ❤️ by Steel</span>
        </div>
      </div>
      <div className="mt-12 text-center text-xs text-dark-400">
        © 2026 DrusaBota • DiscBot • Made with ❤️ by Steel • Design inspired by Nightmare Bots
      </div>
    </footer>
  );
}
