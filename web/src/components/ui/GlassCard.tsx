import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export default function GlassCard({
  children,
  className,
  hover = false,
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "glass rounded-xl p-4",
        hover && "glass-hover cursor-pointer transition-all duration-200",
        className,
      )}
    >
      {children}
    </div>
  );
}
