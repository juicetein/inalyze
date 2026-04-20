import type { InsightItem, InsightPayload } from "../types";

interface InsightsSectionProps {
  insights: InsightPayload;
}

function InsightGroup({
  title,
  helper,
  className,
  items,
}: {
  title: string;
  helper: string;
  className: string;
  items: InsightItem[];
}) {
  if (items.length === 0) {
    return (
      <div className={`insight-group ${className}`}>
        <div className="section-heading-row">
          <div>
            <h3>{title}</h3>
            <p className="group-helper">{helper}</p>
          </div>
        </div>
        <p className="muted-text">Nothing strong enough to show here yet from this upload.</p>
      </div>
    );
  }

  return (
    <div className={`insight-group ${className}`}>
      <div className="section-heading-row">
        <div>
          <h3>{title}</h3>
          <p className="group-helper">{helper}</p>
        </div>
      </div>
      <div className="insight-list">
        {items.map((item) => (
          <article key={`${item.title}-${item.evidence_label}`} className="insight-card">
            <div className="insight-meta-row">
              <span className={`pill pill-${item.severity}`}>{item.evidence_label}</span>
              <span className="confidence-label">{item.confidence} confidence</span>
            </div>
            <h4>{item.title}</h4>
            <p>{item.statement}</p>
            <p className="insight-subtext">{item.why_it_matters}</p>
            <p className="insight-action">
              <strong>Next step:</strong> {item.recommended_action}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}

export function InsightsSection({ insights }: InsightsSectionProps) {
  return (
    <section className="panel insights-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Summary Insights</p>
          <h2>What deserves your attention first</h2>
          <p className="section-helper">
            These are the strongest signals from the uploaded data, ranked to help a business owner
            decide what to look at next.
          </p>
        </div>
        {insights.suppressed_due_to_small_dataset ? (
          <span className="pill pill-neutral">Some softer insights were suppressed on this small dataset</span>
        ) : null}
      </div>

      <div className="insight-grid">
        <InsightGroup
          title="Key Wins"
          helper="What is already working well in the business."
          className="wins-group"
          items={insights.key_wins}
        />
        <InsightGroup
          title="Risks / Issues"
          helper="What may need attention, review, or cleanup."
          className="risks-group"
          items={insights.risks_issues}
        />
        <InsightGroup
          title="Recommended Actions"
          helper="The clearest next steps tied directly to the data."
          className="actions-group"
          items={insights.recommended_actions}
        />
      </div>
    </section>
  );
}
