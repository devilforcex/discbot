import { Link } from "react-router-dom";
import { useAuthStore } from "../hooks/use-auth-store";
import HeroSection from "../features/landing/HeroSection";
import SupportedSources from "../features/landing/SupportedSources";
import WhyDiscBot from "../features/landing/WhyDiscBot";
import StatsSection from "../features/landing/StatsSection";
import Footer from "../features/landing/Footer";

export default function LandingPage() {
  const token = useAuthStore((s) => s.token);

  return (
    <div className="min-h-screen bg-dark-900 text-dark-200">
      {/* Ambient background glow */}
      <div className="pointer-events-none fixed left-1/2 top-0 -z-10 h-[500px] w-[600px] -translate-x-1/2 rounded-full bg-accent-blue-600/15 blur-[160px]" />

      {/* Nav */}
      <nav className="fixed top-0 z-50 w-full border-b border-dark-500 bg-dark-900/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="group flex items-center gap-2">
            <div className="w-8 h-8 rounded-[11px] bg-gradient-to-br from-accent-blue-600 to-accent-blue-300 flex items-center justify-center transition-shadow group-hover:shadow-[0_0_15px_rgba(28,126,239,0.5)]">
              <span className="text-white font-black text-xs">DB</span>
            </div>
            <span className="text-lg font-medium tracking-tight text-white">
              DiscBot
            </span>
          </Link>
          <div className="hidden items-center gap-8 text-sm font-medium text-dark-300 md:flex">
            <a href="#sources" className="hover:text-white transition-colors">Sources</a>
            <a href="#features" className="hover:text-white transition-colors">Features</a>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to={token ? "/dashboard" : "/?connect=1"}
              className="rounded-[11px] bg-gradient-to-r from-accent-blue-600 via-accent-blue to-accent-blue-300 px-4 py-2 text-xs font-semibold tracking-wide text-white transition-all hover:scale-105 active:scale-95 shadow-[0_0_16px_rgba(28,126,239,0.35)]"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main>
        <HeroSection />
        <div id="sources">
          <SupportedSources />
        </div>
        <div id="features">
          <WhyDiscBot />
        </div>
        <StatsSection />
      </main>

      <Footer />
    </div>
  );
}