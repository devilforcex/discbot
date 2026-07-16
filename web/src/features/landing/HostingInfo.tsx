import { Server, Globe, SlidersHorizontal } from "lucide-react";

const items = [
  {
    icon: Server,
    color: "text-accent-violet bg-accent-violet/10",
    title: "Bot process",
    description:
      "Python + Lavalink need always-on host (VPS, home server, systemd). Not GitHub Pages.",
  },
  {
    icon: Globe,
    color: "text-accent-fuchsia bg-accent-fuchsia/10",
    title: "Landing free",
    description:
      "This site deploys free on GitHub Pages or Netlify — no secrets in static files.",
  },
  {
    icon: SlidersHorizontal,
    color: "text-accent-blue bg-accent-blue/10",
    title: "Live dashboard",
    description:
      "FastAPI panel on the same machine as the bot (DASHBOARD_ENABLED=true), bound to localhost or reverse proxy.",
  },
];

export default function HostingInfo() {
  return (
    <section
      id="hosting"
      className="border-y border-white/5 bg-dark-800/20 px-6 py-24"
    >
      <div className="mx-auto grid max-w-7xl gap-12 md:grid-cols-3">
        {items.map((item) => (
          <div key={item.title}>
            <div
              className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-full ${item.color}`}
            >
              <item.icon className="h-5 w-5" />
            </div>
            <h3 className="mb-2 text-lg font-medium text-white">{item.title}</h3>
            <p className="text-sm leading-relaxed text-dark-300">
              {item.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
