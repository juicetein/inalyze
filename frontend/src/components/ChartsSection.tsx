import { formatCurrency } from "../lib/format";
import type { AnalyticsSummary, CategorySeriesPoint, TimeSeriesPoint } from "../types";

interface ChartsSectionProps {
  analytics: AnalyticsSummary;
}

function MiniLineChart({ data }: { data: TimeSeriesPoint[] }) {
  if (data.length === 0) {
    return <p className="muted-text">No dated revenue points available yet.</p>;
  }

  const width = 480;
  const height = 180;
  const maxRevenue = Math.max(...data.map((point) => point.revenue), 1);
  const stepX = data.length > 1 ? width / (data.length - 1) : width;

  const points = data
    .map((point, index) => {
      const x = index * stepX;
      const y = height - (point.revenue / maxRevenue) * (height - 20) - 10;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="line-chart" role="img" aria-label="Sales over time">
        <line x1="0" y1={height - 12} x2={width} y2={height - 12} stroke="rgba(22, 49, 42, 0.12)" />
        <polyline fill="none" stroke="#196c5f" strokeWidth="4" points={points} />
      </svg>
      <div className="chart-footer-row">
        {data.map((point) => (
          <div key={point.date} className="chart-footer-item">
            <span>{point.date}</span>
            <strong>{formatCurrency(point.revenue)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function BarList({
  data,
  label,
}: {
  data: CategorySeriesPoint[];
  label: string;
}) {
  if (data.length === 0) {
    return <p className="muted-text">No values available for this chart.</p>;
  }

  const maxValue = Math.max(...data.map((item) => item.revenue), 1);

  return (
    <div className="bar-list">
      {data.map((item) => (
        <div className="bar-row" key={`${label}-${item.label}`}>
          <div className="bar-row-header">
            <span>{item.label}</span>
            <strong>{formatCurrency(item.revenue)}</strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(item.revenue / maxValue) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusBreakdownChart({ analytics }: { analytics: AnalyticsSummary }) {
  const items = analytics.charts.status_breakdown;
  if (items.length === 0) {
    return <p className="muted-text">No status breakdown available yet.</p>;
  }

  return (
    <div className="status-chart-list">
      {items.map((item) => (
        <div className="status-chart-row" key={`${item.status_type}-${item.status}`}>
          <span className="status-chart-label">
            {item.status_type === "fulfillment" ? "Fulfillment" : "Payment"}: {item.status}
          </span>
          <strong>{item.count}</strong>
        </div>
      ))}
    </div>
  );
}

export function ChartsSection({ analytics }: ChartsSectionProps) {
  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Charts</p>
          <h2>Visualize the cleaned order data</h2>
          <p className="section-helper">
            These simple visuals support the insights above and make the cleaned data easier to scan.
          </p>
        </div>
      </div>

      <div className="charts-grid">
        <article className="chart-card">
          <h3>Sales Over Time</h3>
          <p className="chart-helper">Track how revenue changes across dated orders in the upload.</p>
          <MiniLineChart data={analytics.charts.sales_over_time} />
        </article>

        <article className="chart-card">
          <h3>Revenue by Product</h3>
          <p className="chart-helper">See which products are contributing the most revenue.</p>
          <BarList data={analytics.charts.revenue_by_product} label="product" />
        </article>

        <article className="chart-card">
          <h3>Status Breakdown</h3>
          <p className="chart-helper">Review how fulfillment and payment states are distributed.</p>
          <StatusBreakdownChart analytics={analytics} />
        </article>
      </div>
    </section>
  );
}
