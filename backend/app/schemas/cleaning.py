from typing import Literal

from pydantic import BaseModel, Field


class CanonicalOrderRow(BaseModel):
    row_number: int
    order_id: str | None = None
    customer_identifier: str | None = None
    product_name: str | None = None
    quantity: float | None = None
    order_total: float | None = None
    order_date: str | None = None
    fulfillment_status: str = "unknown"
    payment_status: str = "unknown"
    original_values: dict[str, str] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)


class CleanedDataset(BaseModel):
    canonical_schema_version: str = "v1"
    row_count: int
    rows: list[CanonicalOrderRow]


class TransformationLogEntry(BaseModel):
    row_number: int
    field: str
    action: Literal["normalized", "filled_missing", "flagged", "preserved"]
    original_value: str | None = None
    cleaned_value: str | float | None = None
    note: str


class TransformationAuditSummary(BaseModel):
    total_changes: int = 0
    flagged_row_count: int = 0
    field_change_counts: dict[str, int] = Field(default_factory=dict)
    entries: list[TransformationLogEntry] = Field(default_factory=list)
