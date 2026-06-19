import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse

from src.config import settings
from src.database import SessionLocal, init_db, seed_cards
from src.routes.access import router as access_router
from src.routes.passage import router as passage_router
from src.schemas import ErrorDetail, ErrorResponse
from src.services.offline import load_whitelist
from src.integrations.bulk_sync import start_background_sync
from src.middleware.rate_limiter import RateLimiterMiddleware
from src.middleware.auth import AuthMiddleware

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    init_db()
    db = SessionLocal()
    try:
        seed_cards(db)
    finally:
        db.close()

    # Contract B6 additions
    load_whitelist()
    start_background_sync()

    # MQTT additions
    from src.integrations.mqtt_client import start_mqtt_client
    start_mqtt_client()

    logger.info("Access Gate Service started on port %s", settings.port)
    yield
    logger.info("Access Gate Service stopped")


app = FastAPI(
    title="Access Gate Service",
    description="Smart Campus Operations Platform - Product B - Nhóm B3",
    version="1.0.0",
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimiterMiddleware)

# Routers
app.include_router(access_router)
app.include_router(passage_router)


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the static HTML dashboard."""
    return FileResponse("src/static/index.html")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    details = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INVALID_REQUEST",
                message="Request validation failed",
                details=details,
            )
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code="HTTP_ERROR", message=str(exc.detail))
        ).model_dump(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=settings.host, port=settings.port, reload=settings.env == "development")
