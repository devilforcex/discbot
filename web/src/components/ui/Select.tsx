import type { SelectHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export default function Select({ label, options, className, ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-sm font-medium text-dark-300">{label}</label>
      )}
      <select
        className={cn(
          "rounded-lg border border-dark-500 bg-dark-700 px-3 py-2 text-sm text-dark-100",
          "focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet/30",
          "transition-colors duration-150",
          className,
        )}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
