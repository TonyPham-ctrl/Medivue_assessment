from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.models.payload import ReadingWrapper
from src.models.enums import IngestionStatus
from src.service.ingestion_service import IngestionService

router = APIRouter()
service = IngestionService()

_STATUS_MAP = {
    IngestionStatus.SUCCESS: 200,
    IngestionStatus.INVALID: 400,
    IngestionStatus.DUPLICATE: 409,
    IngestionStatus.ERROR: 500,
}

@router.post("/readings")
def ingest(payload: ReadingWrapper):
    try:
        status, response = service.process(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=response, status_code=_STATUS_MAP.get(status, 200))
