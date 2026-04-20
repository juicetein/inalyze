import type { UploadResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export async function uploadCsv(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/uploads/csv`, {
    method: "POST",
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    const detail = payload?.detail;
    const message =
      typeof detail?.message === "string"
        ? detail.message
        : "Something went wrong while processing your CSV.";
    throw new Error(message);
  }

  return payload as UploadResponse;
}
