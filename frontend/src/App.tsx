import { useState } from "react";
import { ChartsSection } from "./components/ChartsSection";
import { CleanedDataPreview } from "./components/CleanedDataPreview";
import { DataQualitySection } from "./components/DataQualitySection";
import { InsightsSection } from "./components/InsightsSection";
import { KpiGrid } from "./components/KpiGrid";
import { LoadingState } from "./components/LoadingState";
import { UploadPanel } from "./components/UploadPanel";
import { uploadCsv } from "./lib/api";
import type { UploadResponse } from "./types";
import "./App.css";

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please choose a CSV file before uploading.");
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const payload = await uploadCsv(selectedFile);
      setResult(payload);
    } catch (uploadError) {
      const message =
        uploadError instanceof Error
          ? uploadError.message
          : "Something went wrong while processing your CSV.";
      setError(message);
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <main className="page">
        <UploadPanel
          selectedFile={selectedFile}
          error={error}
          isLoading={isLoading}
          onFileChange={setSelectedFile}
          onUpload={handleUpload}
        />

        {isLoading ? <LoadingState /> : null}

        {!isLoading && !result ? (
          <section className="panel empty-state-panel">
            <div className="section-heading-row">
              <div>
                <p className="eyebrow">What You Will Get</p>
                <h2>A fast, owner-friendly readout from one messy CSV</h2>
                <p className="section-helper">
                  Inalyze is designed to feel more like a business assistant than a spreadsheet
                  tool. Upload one order export and the app will surface the most important wins,
                  risks, and next steps first.
                </p>
              </div>
            </div>
            <div className="empty-state-grid">
              <article className="empty-state-card">
                <h3>1. Validate the file</h3>
                <p>Check whether the CSV can be read safely and identify missing or suspicious data.</p>
              </article>
              <article className="empty-state-card">
                <h3>2. Clean the order rows</h3>
                <p>Standardize dates, product names, status fields, and totals into a usable dataset.</p>
              </article>
              <article className="empty-state-card">
                <h3>3. Show business-ready answers</h3>
                <p>Highlight what is working, what looks risky, and what to do next in plain language.</p>
              </article>
            </div>
          </section>
        ) : null}

        {result ? (
          <div className="results-stack">
            <section className="panel result-overview-panel">
              <div className="section-heading-row">
                <div>
                  <p className="eyebrow">Analysis Ready</p>
                  <h2>Your CSV has been processed</h2>
                  <p className="section-helper">
                    Start with the insight cards below, then scan the metrics, charts, data quality,
                    and cleaned preview if you want supporting detail.
                  </p>
                </div>
              </div>
              <div className="message-grid">
                {result.owner_messages.map((message) => (
                  <article
                    key={`${message.level}-${message.title}`}
                    className={`message-card message-${message.level}`}
                  >
                    <p className="message-title">{message.title}</p>
                    <p>{message.detail}</p>
                  </article>
                ))}
              </div>
            </section>
            <InsightsSection insights={result.insights} />
            <KpiGrid analytics={result.analytics} />
            <ChartsSection analytics={result.analytics} />
            <DataQualitySection
              dataQuality={result.data_quality}
              transformationAudit={result.transformation_audit}
            />
            <CleanedDataPreview cleanedDataset={result.cleaned_dataset} />
          </div>
        ) : null}
      </main>
    </div>
  );
}

export default App;
