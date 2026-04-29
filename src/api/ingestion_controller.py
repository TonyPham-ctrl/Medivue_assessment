from fastapi import APIRouter, HTTPException
from src.models import payload
from src.service.ingestion_service import IngestionService

router = APIRouter()
service = IngestionService()

@router.post("/readings")
def ingest(payload: payload.ReadingWrapper):
    try:
        status_code, response = service.process(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    return response
