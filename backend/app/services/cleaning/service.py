from app.schemas.cleaning import (
    CanonicalOrderRow,
    CleanedDataset,
    TransformationAuditSummary,
    TransformationLogEntry,
)
from app.schemas.validation import ColumnInferenceResult
from app.services.cleaning.normalizers import (
    DateNormalizer,
    NumericNormalizer,
    ProductNormalizer,
    StatusNormalizer,
)


class CleaningService:
    def __init__(self) -> None:
        self.product_normalizer = ProductNormalizer()
        self.numeric_normalizer = NumericNormalizer()
        self.date_normalizer = DateNormalizer()
        self.status_normalizer = StatusNormalizer()

    def clean(
        self,
        rows: list[dict[str, str]],
        inferred_columns: list[ColumnInferenceResult],
    ) -> tuple[CleanedDataset, TransformationAuditSummary]:
        role_map = {item.role: item.column_name for item in inferred_columns if item.column_name}
        cleaned_rows: list[CanonicalOrderRow] = []
        entries: list[TransformationLogEntry] = []
        field_change_counts: dict[str, int] = {}
        flagged_row_count = 0

        for row_number, row in enumerate(rows, start=1):
            cleaned_row = CanonicalOrderRow(
                row_number=row_number,
                original_values=row.copy(),
            )

            cleaned_row.order_id = self._clean_text(
                row_number,
                "order_id",
                row.get(role_map["order_id"]) if role_map.get("order_id") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
            )
            cleaned_row.customer_identifier = self._clean_text(
                row_number,
                "customer_identifier",
                row.get(role_map["customer"]) if role_map.get("customer") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
            )
            cleaned_row.product_name = self._clean_product(
                row_number,
                row.get(role_map["product"]) if role_map.get("product") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
            )
            cleaned_row.quantity = self._clean_numeric(
                row_number,
                "quantity",
                row.get(role_map["quantity"]) if role_map.get("quantity") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
            )
            cleaned_row.order_total = self._clean_numeric(
                row_number,
                "order_total",
                row.get(role_map["price"]) if role_map.get("price") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
            )
            cleaned_row.order_date = self._clean_date(
                row_number,
                row.get(role_map["date"]) if role_map.get("date") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
            )
            cleaned_row.fulfillment_status = self._clean_status(
                row_number,
                "fulfillment_status",
                row.get(role_map["fulfillment_status"]) if role_map.get("fulfillment_status") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
                kind="fulfillment",
            )
            cleaned_row.payment_status = self._clean_status(
                row_number,
                "payment_status",
                row.get(role_map["payment_status"]) if role_map.get("payment_status") else None,
                entries,
                field_change_counts,
                cleaned_row.flags,
                kind="payment",
            )

            if cleaned_row.flags:
                flagged_row_count += 1

            cleaned_rows.append(cleaned_row)

        audit = TransformationAuditSummary(
            total_changes=len(entries),
            flagged_row_count=flagged_row_count,
            field_change_counts=field_change_counts,
            entries=entries,
        )
        dataset = CleanedDataset(row_count=len(cleaned_rows), rows=cleaned_rows)
        return dataset, audit

    def _clean_text(
        self,
        row_number: int,
        field: str,
        raw_value: str | None,
        entries: list[TransformationLogEntry],
        field_change_counts: dict[str, int],
        flags: list[str],
    ) -> str | None:
        if raw_value is None:
            flags.append(f"missing_{field}")
            return None

        cleaned = raw_value.strip()
        if not cleaned:
            flags.append(f"missing_{field}")
            return None

        if cleaned != raw_value:
            self._log_change(
                row_number,
                field,
                "normalized",
                raw_value,
                cleaned,
                "Trimmed surrounding whitespace.",
                entries,
                field_change_counts,
            )
        return cleaned

    def _clean_product(
        self,
        row_number: int,
        raw_value: str | None,
        entries: list[TransformationLogEntry],
        field_change_counts: dict[str, int],
        flags: list[str],
    ) -> str:
        normalized = self.product_normalizer.normalize(raw_value)
        if normalized is None:
            flags.append("missing_product_name")
            self._log_change(
                row_number,
                "product_name",
                "filled_missing",
                raw_value,
                "Unknown Product",
                "Filled a missing product value with a deterministic placeholder.",
                entries,
                field_change_counts,
            )
            return "Unknown Product"

        if raw_value is not None and normalized != raw_value.strip():
            self._log_change(
                row_number,
                "product_name",
                "normalized",
                raw_value,
                normalized,
                "Normalized product naming for consistent grouping.",
                entries,
                field_change_counts,
            )
        return normalized

    def _clean_numeric(
        self,
        row_number: int,
        field: str,
        raw_value: str | None,
        entries: list[TransformationLogEntry],
        field_change_counts: dict[str, int],
        flags: list[str],
    ) -> float | None:
        if raw_value is None or not raw_value.strip():
            flags.append(f"missing_{field}")
            return None

        normalized = self.numeric_normalizer.normalize(raw_value)
        if normalized is None:
            flags.append(f"invalid_{field}")
            self._log_change(
                row_number,
                field,
                "flagged",
                raw_value,
                None,
                "Could not convert this value into a number.",
                entries,
                field_change_counts,
            )
            return None

        raw_compact = raw_value.strip()
        normalized_compact = self._stringify_number(normalized)
        if raw_compact != normalized_compact:
            self._log_change(
                row_number,
                field,
                "normalized",
                raw_value,
                normalized,
                "Standardized a numeric value by removing currency formatting or separators.",
                entries,
                field_change_counts,
            )
        return normalized

    def _clean_date(
        self,
        row_number: int,
        raw_value: str | None,
        entries: list[TransformationLogEntry],
        field_change_counts: dict[str, int],
        flags: list[str],
    ) -> str | None:
        if raw_value is None or not raw_value.strip():
            flags.append("missing_order_date")
            return None

        normalized = self.date_normalizer.normalize(raw_value)
        if normalized is None:
            flags.append("invalid_order_date")
            self._log_change(
                row_number,
                "order_date",
                "flagged",
                raw_value,
                None,
                "Could not standardize this date value reliably.",
                entries,
                field_change_counts,
            )
            return None

        if normalized != raw_value.strip():
            self._log_change(
                row_number,
                "order_date",
                "normalized",
                raw_value,
                normalized,
                "Standardized the date into ISO format.",
                entries,
                field_change_counts,
            )
        return normalized

    def _clean_status(
        self,
        row_number: int,
        field: str,
        raw_value: str | None,
        entries: list[TransformationLogEntry],
        field_change_counts: dict[str, int],
        flags: list[str],
        kind: str,
    ) -> str:
        normalized = (
            self.status_normalizer.normalize_fulfillment(raw_value)
            if kind == "fulfillment"
            else self.status_normalizer.normalize_payment(raw_value)
        )

        if raw_value is None or not raw_value.strip():
            flags.append(f"missing_{field}")
            self._log_change(
                row_number,
                field,
                "filled_missing",
                raw_value,
                normalized,
                "Filled a missing status with 'unknown'.",
                entries,
                field_change_counts,
            )
            return normalized

        if normalized == "unknown":
            flags.append(f"unmapped_{field}")
            self._log_change(
                row_number,
                field,
                "flagged",
                raw_value,
                normalized,
                "The status value did not match the current normalization rules.",
                entries,
                field_change_counts,
            )
            return normalized

        if normalized != raw_value.strip().lower():
            self._log_change(
                row_number,
                field,
                "normalized",
                raw_value,
                normalized,
                "Mapped the source status into a canonical status value.",
                entries,
                field_change_counts,
            )
        return normalized

    @staticmethod
    def _log_change(
        row_number: int,
        field: str,
        action: str,
        original_value: str | None,
        cleaned_value: str | float | None,
        note: str,
        entries: list[TransformationLogEntry],
        field_change_counts: dict[str, int],
    ) -> None:
        entries.append(
            TransformationLogEntry(
                row_number=row_number,
                field=field,
                action=action,
                original_value=original_value,
                cleaned_value=cleaned_value,
                note=note,
            )
        )
        field_change_counts[field] = field_change_counts.get(field, 0) + 1

    @staticmethod
    def _stringify_number(value: float) -> str:
        if value.is_integer():
            return str(int(value))
        return str(value)
