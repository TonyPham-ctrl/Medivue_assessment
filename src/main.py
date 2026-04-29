from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.storage.sqlite_db import init_readings_table, init_patient_glucose_table

# Import routers
from src.api.ingestion_controller import router as ingestion_router
# from src.api.patient_controller import router as patient_router

def init_db():
    init_readings_table()
    init_patient_glucose_table()

def create_app() -> FastAPI:
    app = FastAPI(
        title="CGM Monitoring System",
        description="Hello Medivue",
        version="1.0.0"
    )

    init_db()

    app.include_router(ingestion_router, prefix="", tags=["Ingestion"])
    # app.include_router(patient_router, prefix="", tags=["Patients"])

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()