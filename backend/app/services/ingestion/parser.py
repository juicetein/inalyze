import csv
import io

from app.core.errors import IngestionError
from app.services.ingestion.schemas import ParseResult


class CSVParser:
    ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    DELIMITER_CANDIDATES = [",", ";", "\t", "|"]

    def parse(self, raw_bytes: bytes) -> ParseResult:
        decoded_text, encoding_used = self._decode(raw_bytes)
        delimiter, delimiter_warning = self._detect_delimiter(decoded_text)
        headers, rows, malformed_row_indices = self._read_rows(decoded_text, delimiter)

        if not headers:
            raise IngestionError(
                code="empty_headers",
                message="We could not find usable column headers in this file.",
            )

        return ParseResult(
            headers=headers,
            rows=rows,
            encoding_used=encoding_used,
            delimiter=delimiter,
            delimiter_warning=delimiter_warning,
            malformed_row_indices=malformed_row_indices,
        )

    def _decode(self, raw_bytes: bytes) -> tuple[str, str]:
        last_error: UnicodeDecodeError | None = None
        for encoding in self.ENCODINGS:
            try:
                return raw_bytes.decode(encoding), encoding
            except UnicodeDecodeError as exc:
                last_error = exc

        raise IngestionError(
            code="decode_failed",
            message="We couldn't read this file because its text encoding appears to be unsupported.",
        ) from last_error

    def _detect_delimiter(self, text: str) -> tuple[str, str | None]:
        sample = "\n".join(text.splitlines()[:10]).strip()
        if not sample:
            return ",", None

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="".join(self.DELIMITER_CANDIDATES))
            return dialect.delimiter, self._build_delimiter_warning(sample, dialect.delimiter)
        except csv.Error:
            counts = {candidate: sample.count(candidate) for candidate in self.DELIMITER_CANDIDATES}
            detected = max(counts, key=counts.get)
            delimiter = detected if counts[detected] > 0 else ","
            return delimiter, self._build_delimiter_warning(sample, delimiter)

    def _read_rows(self, text: str, delimiter: str) -> tuple[list[str], list[dict[str, str]], list[int]]:
        stream = io.StringIO(text, newline="")
        headers: list[str] = []
        rows: list[dict[str, str]] = []
        malformed_row_indices: list[int] = []

        try:
            reader = csv.reader(stream, delimiter=delimiter)
            for row_index, row in enumerate(reader, start=1):
                if row_index == 1:
                    headers = [self._normalize_header(cell) for cell in row if cell is not None]
                    continue

                if not any(cell.strip() for cell in row):
                    continue

                if len(row) != len(headers):
                    malformed_row_indices.append(row_index)

                normalized_row = {
                    headers[idx]: row[idx].strip() if idx < len(row) else ""
                    for idx in range(len(headers))
                }
                rows.append(normalized_row)
        except csv.Error:
            headers, rows, malformed_row_indices = self._read_rows_with_fallback(text, delimiter)

        return headers, rows, malformed_row_indices

    def _read_rows_with_fallback(
        self, text: str, delimiter: str
    ) -> tuple[list[str], list[dict[str, str]], list[int]]:
        headers: list[str] = []
        rows: list[dict[str, str]] = []
        malformed_row_indices: list[int] = []

        for row_index, raw_line in enumerate(text.splitlines(), start=1):
            if not raw_line.strip():
                continue

            try:
                parsed_line = next(csv.reader([raw_line], delimiter=delimiter))
            except csv.Error:
                parsed_line = raw_line.split(delimiter)
                malformed_row_indices.append(row_index)

            if row_index == 1:
                headers = [self._normalize_header(cell) for cell in parsed_line if cell is not None]
                continue

            if len(parsed_line) != len(headers):
                malformed_row_indices.append(row_index)

            normalized_row = {
                headers[idx]: parsed_line[idx].strip() if idx < len(parsed_line) else ""
                for idx in range(len(headers))
            }
            rows.append(normalized_row)

        return headers, rows, sorted(set(malformed_row_indices))

    @staticmethod
    def _normalize_header(value: str) -> str:
        return value.strip()

    def _build_delimiter_warning(self, sample: str, detected_delimiter: str) -> str | None:
        counts = {candidate: sample.count(candidate) for candidate in self.DELIMITER_CANDIDATES}
        competing = [
            candidate for candidate, count in counts.items() if candidate != detected_delimiter and count > 0
        ]
        if competing:
            return (
                "We detected mixed delimiter characters in the file preview. "
                f"The parser used '{detected_delimiter}' as the best match."
            )
        return None
