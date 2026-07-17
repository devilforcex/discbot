import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Music,
  BarChart3,
  Library,
  Settings,
} from "lucide-react";
import { cn } from "../../lib/utils";
import GuildSelector from "../shared/GuildSelector";

const navItems = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/player", label: "Player", icon: Music },
  { to: "/stats", label: "Statistics", icon: BarChart3 },
  { to: "/library", label: "Library", icon: Library },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-dark-500 bg-dark-800 p-4 lg:flex">
      <div className="mb-6 flex items-center gap-3 px-2">
        <img
          src="/assets/steel-avatar.png"
          alt="DrusaBoT"
          className="h-9 w-9 rounded-full"
        />
        <span className="text-lg font-semibold text-dark-100 font-[family-name:var(--font-heading)]">DrusaBoT</span>
      </div>

      <div className="mb-4 px-2">
        <GuildSelector />
      </div>

      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-[11px] px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent-violet/10 text-accent-violet border border-accent-violet/20"
                  : "text-dark-300 hover:bg-dark-600 hover:text-dark-100",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto border-t border-dark-500 pt-4">
        <NavLink
          to="/"
          className="flex items-center gap-2 px-3 text-sm text-dark-400 hover:text-dark-200"
        >
          Back to Home
        </NavLink>
      </div>
    </aside>
  );
}
