interface PageHeaderProps {
  title: string;
  description?: string;
}

export default function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-dark-100 font-[family-name:var(--font-heading)] text-shadow-heading">{title}</h1>
      {description && (
        <p className="mt-1 text-sm text-dark-300">{description}</p>
      )}
    </div>
  );
}
