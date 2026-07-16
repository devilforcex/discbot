import { cn } from "../../lib/utils";

interface StatusBadgeProps {
  label: string;
  status: "ok" | "warn" | "error" | "idle";
  className?: string;
}

const statusColors = {
  ok: "bg-accent-emerald",
  warn: "bg-accent-amber",
  error: "bg-accent-red",
  idle: "bg-dark-400",
};

export default function StatusBadge({ label, status, className }: StatusBadgeProps) {
  return (
    <div className={cn("flex items-center gap-2 text-sm", className)}>
      <span className={cn("h-2 w-2 rounded-full", statusColors[status])} />
      <span className="text-dark-300">{label}</span>
    </div>
  );
}
