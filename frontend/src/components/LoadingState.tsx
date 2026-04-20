export function LoadingState() {
  return (
    <section className="panel loading-panel">
      <div className="spinner-wrap">
        <div className="spinner" aria-hidden="true" />
      </div>
      <div className="loading-copy">
        <h2>Processing your order data</h2>
        <p className="section-helper">
          This usually takes just a few seconds. We are moving from raw CSV rows to cleaned data,
          metrics, and owner-friendly recommendations.
        </p>
        <div className="loading-steps">
          <span>Checking the file</span>
          <span>Standardizing the rows</span>
          <span>Calculating metrics</span>
          <span>Preparing insights</span>
        </div>
        <p>
          Inalyze is validating the CSV, cleaning the rows, calculating key metrics, and preparing
          business insights.
        </p>
      </div>
    </section>
  );
}
