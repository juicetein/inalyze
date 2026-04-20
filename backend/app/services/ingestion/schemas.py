from dataclasses import dataclass, field


@dataclass
class ParseResult:
    headers: list[str]
    rows: list[dict[str, str]]
    encoding_used: str
    delimiter: str
    delimiter_warning: str | None = None
    malformed_row_indices: list[int] = field(default_factory=list)


@dataclass
class StoredUpload:
    file_id: str
    original_filename: str
    stored_filename: str
    stored_path: str
    metadata_path: str
    content_type: str
    size_bytes: int
