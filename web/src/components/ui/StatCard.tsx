import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  className?: string;
}

export default function StatCard({
  icon,
  label,
  value,
  sub,
  className,
}: StatCardProps) {
  return (
    <div className={cn("glass rounded-xl p-4", className)}>
      <div className="mb-3 flex items-center gap-2 text-dark-300">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-2xl font-semibold text-dark-100">{value}</div>
      {sub && <div className="mt-1 text-xs text-dark-400">{sub}</div>}
    </div>
  );
}
