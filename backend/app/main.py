import base64
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from secrets import compare_digest

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import Response

from app.api.v1 import benchmark, diagnostic, report
from app.core.config import get_settings
from app.core.database import close_db_pool, init_db_pool
from app.core.logging import get_logger, setup_logging
from app.core.security import limiter
from app.deps import AiClientDep
from app.models.schemas import HealthResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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
    docs_visible = (
        settings.debug
        or settings.environment != "production"
        or bool(settings.swagger_password)
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if docs_visible else None,
        redoc_url="/redoc" if docs_visible else None,
        openapi_url="/openapi.json" if docs_visible else None,
    )

    if settings.swagger_password:
        _DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}
        expected = "Basic " + base64.b64encode(
            f"swagger:{settings.swagger_password}".encode()
        ).decode()

        @app.middleware("http")
        async def protect_docs(
            request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            if request.url.path in _DOCS_PATHS or request.url.path.startswith(
                ("/docs/", "/redoc/")
            ):
                if not compare_digest(
                request.headers.get("Authorization", ""), expected
            ):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Authentication required"},
                        headers={"WWW-Authenticate": 'Basic realm="Swagger docs"'},
                    )
            return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

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

    @app.get("/health/ai", tags=["health"])
    async def ai_health_check(ai_client: AiClientDep) -> dict[str, str]:
        """Reporta si el servicio de análisis IA responde (probe al servidor)."""
        healthy = await ai_client.health_check()
        return {"status": "ok" if healthy else "unavailable"}

    return app


app = create_app()
