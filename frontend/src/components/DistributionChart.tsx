interface DistributionChartProps {
  title: string;
  eyebrow: string;
  data: Record<string, number>;
}

export default function DistributionChart({
  title,
  eyebrow,
  data,
}: DistributionChartProps) {
  const entries = Object.entries(data)
    .sort((a, b) => b[1] - a[1]);

  const total = entries.reduce(
    (sum, [, count]) => sum + count,
    0
  );

  if (entries.length === 0) {
    return (
      <section className="analytics-card">
        <p className="section-eyebrow">
          {eyebrow}
        </p>

        <h2>{title}</h2>

        <div className="chart-empty">
          No data available.
        </div>
      </section>
    );
  }

  return (
    <section className="analytics-card">
      <div className="analytics-card__header">
        <div>
          <p className="section-eyebrow">
            {eyebrow}
          </p>

          <h2>{title}</h2>
        </div>

        <span className="analytics-total">
          {total} events
        </span>
      </div>

      <div className="distribution-chart">
        {entries.map(([label, count]) => {
          const percentage =
            total > 0
              ? (count / total) * 100
              : 0;

          return (
            <div
              className="distribution-row"
              key={label}
            >
              <div className="distribution-row__meta">
                <span className="distribution-label">
                  {label}
                </span>

                <span className="distribution-count">
                  {count}
                </span>
              </div>

              <div className="distribution-track">
                <div
                  className="distribution-fill"
                  style={{
                    width: `${percentage}%`,
                  }}
                />
              </div>

              <span className="distribution-percentage">
                {percentage.toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
