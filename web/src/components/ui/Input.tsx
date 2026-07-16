import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export default function Input({ label, className, ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-sm font-medium text-dark-300">{label}</label>
      )}
      <input
        className={cn(
          "rounded-lg border border-dark-500 bg-dark-700 px-3 py-2 text-sm text-dark-100",
          "placeholder:text-dark-400",
          "focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet/30",
          "transition-colors duration-150",
          className,
        )}
        {...props}
      />
    </div>
  );
}
