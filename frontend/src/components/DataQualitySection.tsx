import type { DataQualitySummary, TransformationAuditSummary } from "../types";

interface DataQualitySectionProps {
  dataQuality: DataQualitySummary;
  transformationAudit: TransformationAuditSummary;
}

export function DataQualitySection({
  dataQuality,
  transformationAudit,
}: DataQualitySectionProps) {
  const warnings = dataQuality.issues.slice(0, 5);
  const missingFields =
    dataQuality.missing_required_fields.length > 0
      ? dataQuality.missing_required_fields.map((field) => field.replace(/_/g, " "))
      : ["No missing required fields"];

  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Data Quality</p>
          <h2>What was missing, flagged, or hard to trust</h2>
          <p className="section-helper">
            This helps explain where the results are strong and where the upload may need review.
          </p>
        </div>
      </div>

      <div className="quality-grid">
        <article className="quality-card">
          <h3>Missing Fields</h3>
          <ul className="simple-list">
            {missingFields.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </article>

        <article className="quality-card">
          <h3>Flagged Rows</h3>
          <p className="quality-card-helper">Rows that may need review before acting on every detail.</p>
          <div className="quality-stat-list">
            <p>Validation flags: {dataQuality.suspicious_row_count}</p>
            <p>Cleaning flags: {transformationAudit.flagged_row_count}</p>
            <p>Duplicates: {dataQuality.duplicate_row_count}</p>
            <p>Invalid dates: {dataQuality.invalid_date_count}</p>
            <p>Invalid numbers: {dataQuality.invalid_numeric_value_count}</p>
          </div>
        </article>

        <article className="quality-card">
          <h3>Notable Warnings</h3>
          <p className="quality-card-helper">The most important warnings surfaced during validation.</p>
          {warnings.length > 0 ? (
            <ul className="simple-list">
              {warnings.map((issue) => (
                <li key={issue.code}>
                  {issue.message}
                  {typeof issue.affected_count === "number" ? ` (${issue.affected_count})` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted-text">No major warnings were detected in this upload.</p>
          )}
        </article>
      </div>
    </section>
  );
}
