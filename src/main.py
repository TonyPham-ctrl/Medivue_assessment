from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from src.controllers.ingestion_controller import router as ingestion_router
from src.controllers.patient_controller import router as patient_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="CGM Monitoring System",
        description="Hello Medivue",
        version="1.0.0"
    )

    app.include_router(ingestion_router, prefix="", tags=["Ingestion"])
    app.include_router(patient_router, prefix="", tags=["Patients"])

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()