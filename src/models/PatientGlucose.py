from pydantic import BaseModel


class PatientGlucose(BaseModel):
    patient_id: str
    lower_bound: float
    upper_bound: float