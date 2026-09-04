interface SummaryCardProps {
  label: string;
  value: string | number;
  description: string;
  variant?: "default" | "success" | "warning" | "danger";
}

export default function SummaryCard({
  label,
  value,
  description,
  variant = "default",
}: SummaryCardProps) {
  return (
    <article className={`summary-card summary-card--${variant}`}>
      <div className="summary-card__header">
        <span className="summary-card__label">{label}</span>
      </div>

      <div className="summary-card__value">{value}</div>

      <p className="summary-card__description">
        {description}
      </p>
    </article>
  );
}
