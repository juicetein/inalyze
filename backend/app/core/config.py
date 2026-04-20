from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Inalyze API"
    api_v1_prefix: str = "/api/v1"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    allowed_extensions: set[str] = {".csv"}
    allowed_mime_types: set[str] = {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
    }
    storage_dir: Path = Path(__file__).resolve().parents[2] / "storage"
    raw_uploads_dirname: str = "raw_uploads"
    metadata_dirname: str = "metadata"
    required_roles: tuple[str, ...] = ("order_id", "product", "price", "date")
    suspicious_order_amount_threshold: float = 10000.0
    suspicious_quantity_threshold: float = 100.0


settings = Settings()
