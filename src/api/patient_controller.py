from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.models.enums import IngestionStatus
from src.config import _STATUS_MAP
from src.service.export_service import ExportService

router = APIRouter()
service = ExportService()


@router.get("/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    try:
        export_payload = service.process(patient_id)
        response = {"patient_id": patient_id, "readings": export_payload}
        status = IngestionStatus.SUCCESS
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=response, status_code=_STATUS_MAP.get(status, 200))
