import { cn } from "../../lib/utils";

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
}

export default function ProgressBar({ value, max = 100, className }: ProgressBarProps) {
  const pct = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-dark-500", className)}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-accent-violet to-accent-fuchsia transition-all duration-300"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
