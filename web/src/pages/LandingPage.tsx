import { useState, useEffect } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { Code, LogIn } from "lucide-react";
import { useAuthStore } from "../hooks/use-auth-store";
import ConnectModal from "../components/shared/ConnectModal";
import HeroSection from "../features/landing/HeroSection";
import FeatureCards from "../features/landing/FeatureCards";
import PlayerPreview from "../features/landing/PlayerPreview";
import CommandList from "../features/landing/CommandList";
import HostingInfo from "../features/landing/HostingInfo";
import Footer from "../features/landing/Footer";

export default function LandingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = useAuthStore((s) => s.token);
  const [connectOpen, setConnectOpen] = useState(false);

  useEffect(() => {
    if (searchParams.get("connect") === "1") {
      setConnectOpen(true);
      searchParams.delete("connect");
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const handleConnectSuccess = () => {
    const from = searchParams.get("from");
    if (from) {
      navigate(from);
    } else {
      navigate("/dashboard");
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 text-dark-200">
      {/* Ambient glow */}
      <div className="pointer-events-none fixed left-1/2 top-0 -z-10 h-[500px] w-[600px] -translate-x-1/2 rounded-full bg-accent-violet/15 blur-[160px]" />

      {/* Nav */}
      <nav className="fixed top-0 z-50 w-full border-b border-dark-500 bg-dark-900/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link to="/" className="group flex items-center gap-2">
            <img
              src="/assets/steel-avatar.png"
              alt="DiscBot"
              className="h-8 w-8 rounded-[11px] border border-accent-violet/30 object-cover transition-shadow group-hover:shadow-[0_0_15px_rgba(104,31,209,0.5)]"
            />
            <span className="text-lg font-medium tracking-tight text-white font-[family-name:var(--font-heading)]">
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
            <button
              onClick={() => setConnectOpen(true)}
              className="flex items-center gap-1.5 rounded-[11px] border border-dark-500 px-3 py-2 text-xs font-medium text-dark-300 transition-all hover:border-accent-violet/30 hover:text-white"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Connect</span>
            </button>
            <Link
              to={token ? "/dashboard" : "/?connect=1"}
              className="rounded-[11px] bg-accent-violet px-4 py-2 text-xs font-semibold tracking-wide text-white transition-all hover:bg-accent-violet/80 hover:scale-105 active:scale-95 shadow-[0_0_16px_rgba(104,31,209,0.35)]"
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

      <ConnectModal
        open={connectOpen}
        onClose={() => setConnectOpen(false)}
        onSuccess={handleConnectSuccess}
      />
    </div>
  );
}
