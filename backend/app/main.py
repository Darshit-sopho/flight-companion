from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import airports, flights, tracking


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Flight Companion API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(flights.router)
    app.include_router(tracking.router)
    app.include_router(airports.router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
