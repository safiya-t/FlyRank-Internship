from fastapi import FastAPI, HTTPException, status
from app.config import settings
from app.database import check_db_connection
from app.routes import router

app = FastAPI(
    title="AI Image Understanding & Content Matching Engine",
    description="Backend API for image analysis and semantic content matching",
    version="0.1.0",
)

# Register route handlers
app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    """Basic service health check (no DB/API key dependencies)."""
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"])
def database_health_check():
    """Database connectivity health check with clear error reporting."""
    success, message = check_db_connection()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )
    return {"status": "ok", "database": "connected"}
