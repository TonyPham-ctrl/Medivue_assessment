from fastapi import APIRouter, HTTPException
from src.models import payload
from src.services.ingestion_service import IngestionService

router = APIRouter()
service = IngestionService()

@router.post("/readings")
def ingest(payload: payload.ReadingWrapper):
    try:
        return service.process(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))