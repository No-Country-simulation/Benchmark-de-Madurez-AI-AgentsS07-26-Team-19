from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import benchmark, diagnostic, report
from app.core.config import get_settings
from app.core.database import close_db_pool, init_db_pool
from app.core.logging import get_logger, setup_logging
from app.models.schemas import HealthResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging()
    logger.info("starting_app", environment=settings.environment)

    await init_db_pool(settings)
    logger.info("database_pool_ready")

    yield

    await close_db_pool()
    logger.info("app_shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug or settings.environment != "production" else None,
        redoc_url="/redoc" if settings.debug or settings.environment != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(diagnostic.router, prefix=settings.api_v1_prefix)
    app.include_router(benchmark.router, prefix=settings.api_v1_prefix)
    app.include_router(report.router, prefix=settings.api_v1_prefix)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=settings.app_version,
            environment=settings.environment,
        )

    return app


app = create_app()
