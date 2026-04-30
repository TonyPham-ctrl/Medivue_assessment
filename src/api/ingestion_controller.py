from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.models.payload import ReadingWrapper
from src.service.ingestion_service import IngestionService
from src.config import _STATUS_MAP

router = APIRouter()
service = IngestionService()


@router.post("/readings")
async def ingest(payload: ReadingWrapper):
    arrival_time = datetime.now(timezone.utc)
    try:
        status, response = await service.process(payload, arrival_time)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=response, status_code=_STATUS_MAP.get(status, 200))
