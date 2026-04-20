import re
from collections import defaultdict
from datetime import datetime

from dateutil import parser as date_parser

from app.services.ingestion.constants import (
    FULFILLMENT_KEYWORDS,
    PAYMENT_KEYWORDS,
    ROLE_ALIASES,
)
from app.schemas.validation import ColumnInferenceResult


class ColumnInferenceService:
    def infer(self, headers: list[str], rows: list[dict[str, str]]) -> list[ColumnInferenceResult]:
        results: list[ColumnInferenceResult] = []
        assigned_columns: set[str] = set()

        for role in ROLE_ALIASES:
            column_name, confidence, reason = self._infer_role(role, headers, rows, assigned_columns)
            if column_name:
                assigned_columns.add(column_name)

            results.append(
                ColumnInferenceResult(
                    role=role,
                    column_name=column_name,
                    confidence=confidence,
                    reason=reason,
                )
            )

        return results

    def _infer_role(
        self,
        role: str,
        headers: list[str],
        rows: list[dict[str, str]],
        assigned_columns: set[str],
    ) -> tuple[str | None, str, str]:
        scored_headers: dict[str, float] = defaultdict(float)
        aliases = {self._slug(alias) for alias in ROLE_ALIASES[role]}

        for header in headers:
            if header in assigned_columns:
                continue

            header_slug = self._slug(header)
            if header_slug in aliases:
                scored_headers[header] += 0.8
            elif any(alias in header_slug for alias in aliases):
                scored_headers[header] += 0.45

            scored_headers[header] += self._sample_score(role, header, rows)

        if not scored_headers:
            return None, "unmapped", "No candidate columns were available for this role."

        best_header, best_score = max(scored_headers.items(), key=lambda item: item[1])
        if best_score < 0.45:
            return None, "unmapped", "We could not confidently map this field from the uploaded headers."
        if best_score >= 1.05:
            return best_header, "high", "Header name and sample values strongly match this role."
        if best_score >= 0.7:
            return best_header, "medium", "This column is a likely match based on header name and sample values."
        return best_header, "low", "This column is a possible match, but you may want to review it."

    def _sample_score(self, role: str, header: str, rows: list[dict[str, str]]) -> float:
        values = [row.get(header, "").strip() for row in rows[:25]]
        non_empty = [value for value in values if value]
        if not non_empty:
            return 0.0

        if role == "quantity":
            return 0.4 if self._share_numeric(non_empty) >= 0.8 else 0.0
        if role == "price":
            return 0.45 if self._share_currency_like(non_empty) >= 0.7 else 0.0
        if role == "date":
            return 0.5 if self._share_date_like(non_empty) >= 0.7 else 0.0
        if role == "payment_status":
            return 0.35 if self._share_keywords(non_empty, PAYMENT_KEYWORDS) >= 0.5 else 0.0
        if role == "fulfillment_status":
            return 0.35 if self._share_keywords(non_empty, FULFILLMENT_KEYWORDS) >= 0.5 else 0.0
        if role == "order_id":
            return 0.3 if self._looks_identifier(non_empty) else 0.0
        if role in {"customer", "product"}:
            return 0.2 if self._mostly_text(non_empty) else 0.0
        return 0.0

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    @staticmethod
    def _share_numeric(values: list[str]) -> float:
        valid = 0
        for value in values:
            try:
                float(value.replace(",", "").replace("$", ""))
                valid += 1
            except ValueError:
                continue
        return valid / len(values)

    @staticmethod
    def _share_currency_like(values: list[str]) -> float:
        return sum(1 for value in values if re.search(r"[$€£]|\d", value)) / len(values)

    @staticmethod
    def _share_date_like(values: list[str]) -> float:
        valid = 0
        for value in values:
            try:
                parsed = date_parser.parse(value)
                if parsed <= datetime(2100, 1, 1):
                    valid += 1
            except (ValueError, OverflowError):
                continue
        return valid / len(values)

    @staticmethod
    def _share_keywords(values: list[str], keywords: set[str]) -> float:
        normalized = [value.strip().lower() for value in values]
        return sum(1 for value in normalized if value in keywords) / len(normalized)

    @staticmethod
    def _looks_identifier(values: list[str]) -> bool:
        unique_ratio = len(set(values)) / max(len(values), 1)
        alpha_numeric_ratio = sum(1 for value in values if re.search(r"[a-zA-Z0-9]", value)) / len(values)
        return unique_ratio >= 0.8 and alpha_numeric_ratio >= 0.8

    @staticmethod
    def _mostly_text(values: list[str]) -> bool:
        return sum(1 for value in values if re.search(r"[A-Za-z]", value)) / len(values) >= 0.7
