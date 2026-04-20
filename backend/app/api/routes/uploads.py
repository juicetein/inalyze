from fastapi import APIRouter, File, UploadFile

from app.schemas.validation import UploadValidationResponse
from app.services.ingestion.service import IngestionService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/csv", response_model=UploadValidationResponse)
async def upload_csv(file: UploadFile | None = File(None)) -> UploadValidationResponse:
    service = IngestionService()
    return await service.process_upload(file)
