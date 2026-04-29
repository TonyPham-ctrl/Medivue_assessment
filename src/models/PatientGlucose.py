from pydantic import BaseModel


class PATIENT_GLUCOSE(BaseModel):
    patient_id: str
    lower_bound: float
    upper_bound: float