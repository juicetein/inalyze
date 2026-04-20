import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import settings
from app.services.ingestion.schemas import StoredUpload


class LocalUploadStorage:
    def __init__(self) -> None:
        self.base_dir = settings.storage_dir
        self.raw_dir = self.base_dir / settings.raw_uploads_dirname
        self.metadata_dir = self.base_dir / settings.metadata_dirname
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content_type: str, raw_bytes: bytes) -> StoredUpload:
        file_id = str(uuid.uuid4())
        original_suffix = Path(filename).suffix.lower() or ".csv"
        stored_filename = f"{file_id}{original_suffix}"
        stored_path = self.raw_dir / stored_filename
        metadata_path = self.metadata_dir / f"{file_id}.json"

        stored_path.write_bytes(raw_bytes)

        metadata = {
            "file_id": file_id,
            "original_filename": filename,
            "stored_filename": stored_filename,
            "stored_path": str(stored_path),
            "content_type": content_type,
            "size_bytes": len(raw_bytes),
            "uploaded_at": datetime.now(UTC).isoformat(),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return StoredUpload(
            file_id=file_id,
            original_filename=filename,
            stored_filename=stored_filename,
            stored_path=str(stored_path),
            metadata_path=str(metadata_path),
            content_type=content_type,
            size_bytes=len(raw_bytes),
        )
