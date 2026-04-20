from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.analytics import AnalyticsSummary
from app.schemas.cleaning import CleanedDataset, TransformationAuditSummary
from app.schemas.insights import InsightPayload


class FileMetadata(BaseModel):
    file_id: str
    original_filename: str
    stored_filename: str
    stored_path: str
    content_type: str
    size_bytes: int


class ParsingSummary(BaseModel):
    encoding_used: str
    delimiter: str
    delimiter_warning: str | None = None
    total_rows: int
    parsed_rows: int
    malformed_row_count: int
    malformed_row_indices: list[int] = Field(default_factory=list)


class ColumnInferenceResult(BaseModel):
    role: str
    column_name: str | None = None
    confidence: Literal["high", "medium", "low", "unmapped"]
    reason: str


class QualityIssue(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    affected_count: int | None = None


class DataQualitySummary(BaseModel):
    missing_required_fields: list[str] = Field(default_factory=list)
    missing_value_counts: dict[str, int] = Field(default_factory=dict)
    duplicate_row_count: int = 0
    invalid_numeric_value_count: int = 0
    invalid_date_count: int = 0
    suspicious_row_count: int = 0
    issues: list[QualityIssue] = Field(default_factory=list)


class OwnerMessage(BaseModel):
    level: Literal["success", "warning", "error"]
    title: str
    detail: str


class UploadValidationResponse(BaseModel):
    status: Literal["success", "warning", "error"]
    file_metadata: FileMetadata
    parsing_summary: ParsingSummary
    inferred_columns: list[ColumnInferenceResult]
    data_quality: DataQualitySummary
    cleaned_dataset: CleanedDataset
    transformation_audit: TransformationAuditSummary
    analytics: AnalyticsSummary
    insights: InsightPayload
    owner_messages: list[OwnerMessage]
