import { ChangeEvent } from "react";

interface UploadPanelProps {
  selectedFile: File | null;
  error: string | null;
  isLoading: boolean;
  onFileChange: (file: File | null) => void;
  onUpload: () => void;
}

export function UploadPanel({
  selectedFile,
  error,
  isLoading,
  onFileChange,
  onUpload,
}: UploadPanelProps) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onFileChange(event.target.files?.[0] ?? null);
  };

  return (
    <section className="panel hero-panel">
      <div className="hero-copy">
        <div className="logo-lockup" aria-label="Inalyze">
          <div className="logo-mark" aria-hidden="true">
            <span className="logo-dot logo-dot-large" />
            <span className="logo-dot logo-dot-small" />
          </div>
          <span className="logo-wordmark">Inalyze</span>
        </div>
        <p className="eyebrow">CSV insight pipeline for small businesses</p>
        <h1>Messy order CSVs, turned into decisions.</h1>
        <p className="hero-text">
          Upload a CSV from Shopify, Square, Etsy, Toast, or a spreadsheet export. Inalyze will
          validate the file, clean the order data, and show the most important business wins,
          risks, and actions in plain language.
        </p>
        <div className="hero-points">
          <span className="hero-point">Highlights what is working</span>
          <span className="hero-point">Flags risky or unreliable data</span>
          <span className="hero-point">Suggests the next action to take</span>
        </div>
      </div>

      <div className="upload-card">
        <p className="upload-card-title">Upload one order CSV to begin</p>
        <p className="upload-card-helper">
          Best results come from exports that include order date, product, customer, and total.
        </p>
        <label className="file-input-label" htmlFor="csv-upload">
          Choose CSV File
        </label>
        <input
          id="csv-upload"
          type="file"
          accept=".csv,text/csv"
          onChange={handleChange}
          disabled={isLoading}
        />
        <p className="file-meta">
          {selectedFile ? `Selected: ${selectedFile.name}` : "No file selected yet"}
        </p>
        <button className="primary-button" onClick={onUpload} disabled={!selectedFile || isLoading}>
          {isLoading ? "Processing..." : "Upload and Analyze"}
        </button>
        {error ? (
          <div className="error-banner">
            <strong>Upload could not be processed.</strong>
            <div>{error}</div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
