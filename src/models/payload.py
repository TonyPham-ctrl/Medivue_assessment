from pydantic import BaseModel
from datetime import datetime


class ReadingPayload(BaseModel):
    device_id: str
    patient_id: str
    glucose_mgdl: float
    battery_pct: int
    signal_quality: str  # "good" | "poor" | "degraded"
    recorded_at: datetime


class ReadingWrapper(BaseModel):
    device_id: str
    patient_id: str
    payload: ReadingPayload