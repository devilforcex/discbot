import { cn } from "../../lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  className?: string;
}

export default function EmptyState({ icon, title, description, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 text-center", className)}>
      {icon && <div className="mb-4 text-dark-400">{icon}</div>}
      <h3 className="text-lg font-medium text-dark-200">{title}</h3>
      {description && <p className="mt-1 text-sm text-dark-400">{description}</p>}
    </div>
  );
}
