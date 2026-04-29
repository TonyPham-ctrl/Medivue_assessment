from fastapi import FastAPI
from src.storage.sqlite_db import init_db
from src.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION

# Import routers
from src.api.ingestion_controller import router as ingestion_router
from src.api.patient_controller import router as patient_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION
    )

    init_db()

    app.include_router(ingestion_router, prefix="", tags=["Ingestion"])
    app.include_router(patient_router, prefix="", tags=["Patients"])

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()