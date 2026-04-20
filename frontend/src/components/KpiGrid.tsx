import { formatPercent } from "../lib/format";
import type { AnalyticsSummary } from "../types";

interface KpiGridProps {
  analytics: AnalyticsSummary;
}

export function KpiGrid({ analytics }: KpiGridProps) {
  const cards = [
    {
      label: "Total Revenue",
      value: analytics.total_revenue.formatted_value,
    },
    {
      label: "Order Count",
      value: analytics.order_count.toString(),
    },
    {
      label: "Average Order Value",
      value: analytics.average_order_value.formatted_value,
    },
    {
      label: "Repeat Customer Rate",
      value: formatPercent(analytics.repeat_customer_rate),
    },
  ];

  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">KPI Snapshot</p>
          <h2>Core business metrics</h2>
        </div>
      </div>
      <div className="kpi-grid">
        {cards.map((card) => (
          <article className="kpi-card" key={card.label}>
            <p className="kpi-label">{card.label}</p>
            <p className="kpi-value">{card.value}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
