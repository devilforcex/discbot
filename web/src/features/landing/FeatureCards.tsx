import { Music, PlayCircle, Shield } from "lucide-react";
import GlassCard from "../../components/ui/GlassCard";

const features = [
  {
    icon: Music,
    title: "Lavalink v4",
    description:
      "High-quality streams via Wavelink. YouTube & Spotify URLs, queue, loop, autoplay, volume persistence.",
    tags: ["Low latency", "24/7 mode"],
    iconBg: "bg-accent-violet/10 border-accent-violet/20",
    iconColor: "text-accent-violet",
  },
  {
    icon: PlayCircle,
    title: "Embed player",
    description:
      "Persistent Now Playing with real Discord buttons — pause, skip, loop, volume, favorites — not just text commands.",
    tags: ["Buttons", "Emoji UI"],
    iconBg: "bg-accent-fuchsia/10 border-accent-fuchsia/20",
    iconColor: "text-accent-fuchsia",
  },
  {
    icon: Shield,
    title: "Access control",
    description:
      "Owner, whitelist, blacklist, self-request flow, audit logs. Guild + music channel lock.",
    tags: ["Whitelist", "Audit"],
    iconBg: "bg-accent-blue/10 border-accent-blue/20",
    iconColor: "text-accent-blue",
  },
];

export default function FeatureCards() {
  return (
    <section id="features" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-white md:text-4xl font-[family-name:var(--font-heading)]">
            Built for performance
          </h2>
          <p className="max-w-md text-dark-300">
            Private music bot stack — Lavalink, SQLite, access control, optional
            web dashboard.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {features.map((f) => (
            <GlassCard key={f.title} hover className="p-8 transition-all duration-300">
              <div className={`mb-6 flex h-12 w-12 items-center justify-center rounded-[11px] border ${f.iconBg} ${f.iconColor}`}>
                <f.icon className="h-7 w-7" />
              </div>
              <h3 className="mb-2 text-xl font-medium text-white font-[family-name:var(--font-heading)]">{f.title}</h3>
              <p className="mb-4 text-sm leading-relaxed text-dark-300">
                {f.description}
              </p>
              <div className="flex flex-wrap gap-2">
                {f.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-[8px] border border-dark-500 bg-dark-600 px-2 py-1 text-xs text-dark-300"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
