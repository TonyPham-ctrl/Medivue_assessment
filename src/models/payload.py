from pydantic import BaseModel
from datetime import datetime


class ReadingPayload(BaseModel):
    glucose_mgdl: float
    battery_pct: int
    signal_quality: str  # "good" | "poor" | "degraded"
    recorded_at: datetime


class ReadingWrapper(BaseModel):
    device_id: str
    patient_id: str
    reading: ReadingPayload
