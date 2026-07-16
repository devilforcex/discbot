import { cn } from "../../lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "violet" | "fuchsia" | "blue" | "amber" | "emerald" | "red";
  className?: string;
}

const variantStyles = {
  violet: "bg-accent-violet/15 text-accent-violet",
  fuchsia: "bg-accent-fuchsia/15 text-accent-fuchsia",
  blue: "bg-accent-blue/15 text-accent-blue",
  amber: "bg-accent-amber/15 text-accent-amber",
  emerald: "bg-accent-emerald/15 text-accent-emerald",
  red: "bg-accent-red/15 text-accent-red",
};

export default function Badge({ children, variant = "violet", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
