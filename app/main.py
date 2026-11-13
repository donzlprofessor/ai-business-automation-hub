from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.inquiries import router
from app.core.config import CorsSettings
from app.db import get_db


def create_app(cors: CorsSettings | None = None) -> FastAPI:
    application = FastAPI(title="AI Business Automation Hub", version="0.1.0")
    application.add_middleware(
        CORSMiddleware, allow_origins=(cors or CorsSettings()).cors_origins,
        allow_credentials=False, allow_methods=["GET", "PATCH"],
        allow_headers=["Accept", "Content-Type"],
    )
    application.include_router(router)
    application.add_api_route("/health", health, methods=["GET"], tags=["health"])
    return application


def health(db: Annotated[Session, Depends(get_db)]):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
    return {"status": "healthy"}


app = create_app()
