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

class ExportPayload(BaseModel):
    device_id: str
    patient_id: str
    battery_pct: int
    signal_quality: str
    alert_status: str
    percentage_in_range: float
    summary: list[ReadingPayload]


