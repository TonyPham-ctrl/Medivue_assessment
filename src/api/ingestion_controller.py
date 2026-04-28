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
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=response["message"])
    return response
