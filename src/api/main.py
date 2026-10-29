"""
FastAPI application entrypoint for ApexFin AI.
Configures CORS, global RFC 7807 problem details handlers, and API routes.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.dependencies import get_vector_store
from src.api.routes.analysis import router as analysis_router
from src.api.routes.documents import router as documents_router
from src.config.settings import get_settings
from src.domain.exceptions import ApexFinException, ProblemDetails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes vector storage collections, syncs BM25, and preloads benchmark filings on startup."""
    store = get_vector_store()
    store.ensure_collection(vector_size=384)
    settings = get_settings()

    from src.api.dependencies import get_hybrid_retriever
    from src.ingestion.sample_loader import load_benchmark_samples

    retriever_getter = app.dependency_overrides.get(get_hybrid_retriever, get_hybrid_retriever)
    retriever = retriever_getter()

    # 1. Hidrasi BM25 jika Qdrant sudah memiliki data sebelumnya (mencegah desinkronisasi pasca restart)
    if store.count() > 0 and retriever.bm25_index.count() == 0:
        persisted_chunks = store.get_all_chunks()
        if persisted_chunks:
            retriever.bm25_index.build_index(persisted_chunks)

    # 2. Jika database kosong dan bukan dalam mode testing, muat data benchmark
    if settings.ENVIRONMENT != "testing" and store.count() == 0:
        load_benchmark_samples(retriever)

    yield


def create_app() -> FastAPI:
    """Application factory for ApexFin AI."""
    settings = get_settings()

    app = FastAPI(
        title="ApexFin AI - Financial Intelligence & Audit-Ready Hybrid RAG",
        description="Production API with coordinate-aware parsing, hybrid retrieval, and deterministic fact verification.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 1. Global RFC 7807 Exception Handlers
    @app.exception_handler(ApexFinException)
    async def apexfin_domain_exception_handler(
        request: Request,
        exc: ApexFinException,
    ) -> JSONResponse:
        problem = exc.to_problem_details(instance=str(request.url))
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(),
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        problem = ProblemDetails(
            type="https://apexfin.ai/errors/validation-error",
            title="Request Validation Failed",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The request payload failed schema validation constraints.",
            instance=str(request.url),
            invalid_params=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=problem.model_dump(),
            media_type="application/problem+json",
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        problem = ProblemDetails(
            type="https://apexfin.ai/errors/internal-error",
            title="Internal Server Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) if settings.DEBUG else "An unexpected internal server error occurred.",
            instance=str(request.url),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump(),
            media_type="application/problem+json",
        )

    # 2. Register API Routers
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")

    # 3. Mount Static Assets & Templates
    base_dir = Path(__file__).resolve().parent.parent
    web_dir = base_dir / "web"
    static_dir = web_dir / "static"
    templates_dir = web_dir / "templates"

    static_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    templates = Jinja2Templates(directory=str(templates_dir))

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.head("/", include_in_schema=False)
    async def serve_index(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "healthy", "service": "apexfin-ai", "version": "0.1.0"}

    return app


app = create_app()
