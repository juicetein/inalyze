from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.errors import IngestionError
from app.schemas.validation import FileMetadata, ParsingSummary, UploadValidationResponse
from app.services.analytics.service import AnalyticsService
from app.services.cleaning.service import CleaningService
from app.services.ingestion.inference import ColumnInferenceService
from app.services.ingestion.parser import CSVParser
from app.services.ingestion.storage import LocalUploadStorage
from app.services.ingestion.validation import DatasetValidationService
from app.services.insights.service import InsightService


class IngestionService:
    def __init__(self) -> None:
        self.storage = LocalUploadStorage()
        self.parser = CSVParser()
        self.inference = ColumnInferenceService()
        self.validation = DatasetValidationService()
        self.cleaning = CleaningService()
        self.analytics = AnalyticsService()
        self.insights = InsightService()

    async def process_upload(self, file: UploadFile | None) -> UploadValidationResponse:
        self._validate_upload_metadata(file)
        raw_bytes = await file.read()
        self._validate_upload_size(raw_bytes)

        stored = self.storage.save(
            filename=file.filename or "upload.csv",
            content_type=file.content_type or "application/octet-stream",
            raw_bytes=raw_bytes,
        )

        try:
            parse_result = self.parser.parse(raw_bytes)
            inferred_columns = self.inference.infer(parse_result.headers, parse_result.rows)
            data_quality, owner_messages = self.validation.summarize(
                rows=parse_result.rows,
                inferred_columns=inferred_columns,
                malformed_row_count=len(parse_result.malformed_row_indices),
            )
            cleaned_dataset, transformation_audit = self.cleaning.clean(
                rows=parse_result.rows,
                inferred_columns=inferred_columns,
            )
            analytics = self.analytics.analyze(cleaned_dataset)
            insights = self.insights.generate(
                cleaned_dataset=cleaned_dataset,
                transformation_audit=transformation_audit,
                data_quality=data_quality,
                analytics=analytics,
            )
        except IngestionError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": exc.code, "message": exc.message},
            ) from exc

        status_value = "warning" if data_quality.issues else "success"

        return UploadValidationResponse(
            status=status_value,
            file_metadata=FileMetadata(
                file_id=stored.file_id,
                original_filename=stored.original_filename,
                stored_filename=stored.stored_filename,
                stored_path=stored.stored_path,
                content_type=stored.content_type,
                size_bytes=stored.size_bytes,
            ),
            parsing_summary=ParsingSummary(
                encoding_used=parse_result.encoding_used,
                delimiter=parse_result.delimiter,
                delimiter_warning=parse_result.delimiter_warning,
                total_rows=len(parse_result.rows),
                parsed_rows=len(parse_result.rows),
                malformed_row_count=len(parse_result.malformed_row_indices),
                malformed_row_indices=parse_result.malformed_row_indices,
            ),
            inferred_columns=inferred_columns,
            data_quality=data_quality,
            cleaned_dataset=cleaned_dataset,
            transformation_audit=transformation_audit,
            analytics=analytics,
            insights=insights,
            owner_messages=owner_messages,
        )

    def _validate_upload_metadata(self, file: UploadFile | None) -> None:
        if file is None or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "missing_file",
                    "message": "Please choose a CSV file before uploading.",
                },
            )

        extension = Path(file.filename).suffix.lower()
        if extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "code": "invalid_extension",
                    "message": "Only CSV files are supported right now.",
                },
            )

        if file.content_type and file.content_type not in settings.allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "code": "invalid_mime_type",
                    "message": "This file type does not look like a CSV export.",
                },
            )

    def _validate_upload_size(self, raw_bytes: bytes) -> None:
        if not raw_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "empty_file",
                    "message": "This file is empty. Please upload a CSV with order data.",
                },
            )

        if len(raw_bytes) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "file_too_large",
                    "message": "This file is too large for the current MVP upload limit.",
                },
            )
