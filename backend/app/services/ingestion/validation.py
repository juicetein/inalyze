from datetime import datetime

from dateutil import parser as date_parser

from app.core.config import settings
from app.schemas.validation import (
    ColumnInferenceResult,
    DataQualitySummary,
    OwnerMessage,
    QualityIssue,
)


class DatasetValidationService:
    def summarize(
        self,
        rows: list[dict[str, str]],
        inferred_columns: list[ColumnInferenceResult],
        malformed_row_count: int,
    ) -> tuple[DataQualitySummary, list[OwnerMessage]]:
        role_map = {item.role: item.column_name for item in inferred_columns if item.column_name}
        missing_required_fields = [
            role for role in settings.required_roles if not role_map.get(role)
        ]
        missing_value_counts = self._missing_value_counts(rows)
        duplicate_row_count = self._duplicate_row_count(rows)
        invalid_numeric_value_count = self._invalid_numeric_values(rows, role_map)
        invalid_date_count = self._invalid_dates(rows, role_map)
        suspicious_row_count = self._suspicious_rows(rows, role_map)

        issues: list[QualityIssue] = []
        owner_messages: list[OwnerMessage] = []

        if missing_required_fields:
            issues.append(
                QualityIssue(
                    code="missing_required_fields",
                    severity="error",
                    message=(
                        "We could not confidently identify all of the core business columns needed "
                        "for analysis."
                    ),
                    affected_count=len(missing_required_fields),
                )
            )
            owner_messages.append(
                OwnerMessage(
                    level="error",
                    title="Some core columns could not be identified",
                    detail=(
                        "We could not find clear matches for: "
                        + ", ".join(missing_required_fields).replace("_", " ")
                        + ". Try exporting a file with clearer headers or standard order fields."
                    ),
                )
            )

        if malformed_row_count:
            issues.append(
                QualityIssue(
                    code="malformed_rows",
                    severity="warning",
                    message="Some rows did not match the header layout and may be incomplete.",
                    affected_count=malformed_row_count,
                )
            )
            owner_messages.append(
                OwnerMessage(
                    level="warning",
                    title="Some rows were hard to read",
                    detail=(
                        f"We found {malformed_row_count} row(s) with missing or extra columns. "
                        "We kept reading the file, but those rows should be reviewed."
                    ),
                )
            )

        if duplicate_row_count:
            issues.append(
                QualityIssue(
                    code="duplicate_rows",
                    severity="warning",
                    message="Possible duplicate rows were detected.",
                    affected_count=duplicate_row_count,
                )
            )

        if invalid_numeric_value_count:
            issues.append(
                QualityIssue(
                    code="invalid_numeric_values",
                    severity="warning",
                    message="Some quantity or price values could not be interpreted as numbers.",
                    affected_count=invalid_numeric_value_count,
                )
            )

        if invalid_date_count:
            issues.append(
                QualityIssue(
                    code="invalid_dates",
                    severity="warning",
                    message="Some date values could not be interpreted reliably.",
                    affected_count=invalid_date_count,
                )
            )

        if suspicious_row_count:
            issues.append(
                QualityIssue(
                    code="suspicious_rows",
                    severity="warning",
                    message="Some rows contain unusual values that should be reviewed.",
                    affected_count=suspicious_row_count,
                )
            )

        if not owner_messages:
            owner_messages.append(
                OwnerMessage(
                    level="success",
                    title="Your file was validated successfully",
                    detail="We were able to read the file and identify the main order columns for the next step.",
                )
            )

        summary = DataQualitySummary(
            missing_required_fields=missing_required_fields,
            missing_value_counts=missing_value_counts,
            duplicate_row_count=duplicate_row_count,
            invalid_numeric_value_count=invalid_numeric_value_count,
            invalid_date_count=invalid_date_count,
            suspicious_row_count=suspicious_row_count,
            issues=issues,
        )
        return summary, owner_messages

    @staticmethod
    def _missing_value_counts(rows: list[dict[str, str]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            for key, value in row.items():
                if not value.strip():
                    counts[key] = counts.get(key, 0) + 1
        return counts

    @staticmethod
    def _duplicate_row_count(rows: list[dict[str, str]]) -> int:
        seen: set[tuple[tuple[str, str], ...]] = set()
        duplicates = 0
        for row in rows:
            fingerprint = tuple(sorted(row.items()))
            if fingerprint in seen:
                duplicates += 1
            else:
                seen.add(fingerprint)
        return duplicates

    @staticmethod
    def _invalid_numeric_values(rows: list[dict[str, str]], role_map: dict[str, str]) -> int:
        invalid_count = 0
        for role in ("quantity", "price"):
            column = role_map.get(role)
            if not column:
                continue
            for row in rows:
                value = row.get(column, "").strip()
                if not value:
                    continue
                try:
                    float(value.replace(",", "").replace("$", ""))
                except ValueError:
                    invalid_count += 1
        return invalid_count

    @staticmethod
    def _invalid_dates(rows: list[dict[str, str]], role_map: dict[str, str]) -> int:
        column = role_map.get("date")
        if not column:
            return 0

        invalid_count = 0
        for row in rows:
            value = row.get(column, "").strip()
            if not value:
                continue
            try:
                parsed = date_parser.parse(value)
                if parsed > datetime(2100, 1, 1):
                    invalid_count += 1
            except (ValueError, OverflowError):
                invalid_count += 1
        return invalid_count

    @staticmethod
    def _suspicious_rows(rows: list[dict[str, str]], role_map: dict[str, str]) -> int:
        suspicious = 0
        price_column = role_map.get("price")
        quantity_column = role_map.get("quantity")

        for row in rows:
            row_is_suspicious = False

            if price_column:
                value = row.get(price_column, "").strip()
                if value:
                    try:
                        price = float(value.replace(",", "").replace("$", ""))
                        if price < 0 or price > settings.suspicious_order_amount_threshold:
                            row_is_suspicious = True
                    except ValueError:
                        pass

            if quantity_column:
                value = row.get(quantity_column, "").strip()
                if value:
                    try:
                        quantity = float(value.replace(",", ""))
                        if quantity < 0 or quantity > settings.suspicious_quantity_threshold:
                            row_is_suspicious = True
                    except ValueError:
                        pass

            if row_is_suspicious:
                suspicious += 1

        return suspicious
