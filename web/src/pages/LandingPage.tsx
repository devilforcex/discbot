import { Link } from "react-router-dom";
import { Code } from "lucide-react";
import HeroSection from "../features/landing/HeroSection";
import FeatureCards from "../features/landing/FeatureCards";
import PlayerPreview from "../features/landing/PlayerPreview";
import CommandList from "../features/landing/CommandList";
import HostingInfo from "../features/landing/HostingInfo";
import Footer from "../features/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-dark-900 text-dark-200">
      {/* Ambient glow */}
      <div className="pointer-events-none fixed left-1/4 top-0 -z-10 h-96 w-96 rounded-full bg-accent-violet/20 blur-[128px]" />
      <div className="pointer-events-none fixed bottom-0 right-1/4 -z-10 h-96 w-96 rounded-full bg-accent-fuchsia/10 blur-[128px]" />

      {/* Nav */}
      <nav className="glass fixed top-0 z-50 w-full border-b border-white/5">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link to="/" className="group flex items-center gap-2">
            <img
              src="/assets/steel-avatar.png"
              alt="DiscBot"
              className="h-8 w-8 rounded-lg border border-accent-violet/30 object-cover transition-shadow group-hover:shadow-[0_0_15px_rgba(139,92,246,0.5)]"
            />
            <span className="text-lg font-medium tracking-tight text-white">
              DrusaBota
            </span>
          </Link>
          <div className="hidden items-center gap-8 text-sm font-medium text-dark-300 md:flex">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#player" className="hover:text-white transition-colors">Player</a>
            <a href="#commands" className="hover:text-white transition-colors">Commands</a>
            <a href="#hosting" className="hover:text-white transition-colors">Hosting</a>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/devilforcex/discbot"
              target="_blank"
              rel="noreferrer"
              className="hidden text-dark-300 hover:text-white transition-colors sm:flex"
            >
              <Code className="h-5 w-5" />
            </a>
            <Link
              to="/dashboard"
              className="rounded-lg bg-white px-4 py-2 text-xs font-semibold tracking-wide text-black transition-all hover:bg-zinc-200 hover:scale-105 active:scale-95"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <HeroSection />
      <FeatureCards />
      <PlayerPreview />
      <CommandList />
      <HostingInfo />
      <Footer />
    </div>
  );
}
