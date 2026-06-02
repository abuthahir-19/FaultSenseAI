from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.config import get_settings
from backend.app.utils.logger import setup_logger
from backend.app.rag.vectorstore import get_chroma_store
from backend.app.rag.embeddings import get_embedding_manager
from backend.app.routers import health, query, analyze, incidents, ingest, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logger(settings.LOG_LEVEL)
    logger.info("Starting TelecomNetworkFaultIntel API...")
    get_embedding_manager()
    get_chroma_store()
    logger.info("Singletons initialized.")
    yield
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="TelecomNetworkFaultIntel API",
        description=(
            "AI-Powered Telecom Network Fault Intelligence Assistant. "
            "RAG + LangGraph multi-agent system for root cause analysis and remediation."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(query.router)
    app.include_router(analyze.router)
    app.include_router(incidents.router)
    app.include_router(ingest.router)
    app.include_router(analytics.router)

    return app


app = create_app()
