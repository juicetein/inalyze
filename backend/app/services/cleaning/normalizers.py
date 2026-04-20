import re
from datetime import datetime

from dateutil import parser as date_parser

from app.services.cleaning.constants import FULFILLMENT_STATUS_MAP, PAYMENT_STATUS_MAP


class ProductNormalizer:
    def normalize(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        cleaned = cleaned.replace("_", " ").replace("-", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        tokens = cleaned.split(" ")
        normalized_tokens = [self._normalize_token(token) for token in tokens]
        return " ".join(normalized_tokens)

    @staticmethod
    def _normalize_token(token: str) -> str:
        if token.isupper():
            return token
        if re.fullmatch(r"\d+[a-z]+", token):
            return token
        return token.capitalize()


class NumericNormalizer:
    def normalize(self, value: str | None) -> float | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        negative = cleaned.startswith("(") and cleaned.endswith(")")
        cleaned = cleaned.replace("(", "").replace(")", "")
        cleaned = cleaned.replace("$", "").replace("€", "").replace("£", "")
        cleaned = cleaned.replace(",", "").strip()

        try:
            parsed = float(cleaned)
        except ValueError:
            return None

        return -parsed if negative else parsed


class DateNormalizer:
    def normalize(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        try:
            parsed = date_parser.parse(cleaned)
        except (ValueError, OverflowError):
            return None

        if parsed > datetime(2100, 1, 1):
            return None

        return parsed.date().isoformat()


class StatusNormalizer:
    def normalize_fulfillment(self, value: str | None) -> str:
        return self._normalize(value, FULFILLMENT_STATUS_MAP)

    def normalize_payment(self, value: str | None) -> str:
        return self._normalize(value, PAYMENT_STATUS_MAP)

    @staticmethod
    def _normalize(value: str | None, mapping: dict[str, str]) -> str:
        if value is None:
            return "unknown"

        cleaned = re.sub(r"\s+", " ", value.strip().lower())
        if not cleaned:
            return "unknown"

        return mapping.get(cleaned, "unknown")
