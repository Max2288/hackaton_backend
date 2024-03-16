from fastapi import FastAPI
from loguru import logger

from app.api import api
from app.core.config import Config
from app.middleware.size import LimitUploadSize
from app.on_shutdown import stop_producer
from app.on_startup.kafka import create_producer
from app.on_startup.minio import create_bucket
from app.version import VERSION

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.metrics.metrics import metrics, prometheus_metrics
from app.on_startup.redis import start_redis

logger.add(
    "./logs/sirius.log",
    rotation="50 MB",
    retention=5,
)


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LimitUploadSize, max_upload_size=50_000_000)
    app.middleware("http")(prometheus_metrics)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await start_redis()
    await create_bucket()
    await create_producer()
    logger.info("START APP")
    yield
    await stop_producer()
    logger.info("END APP")


def create_app() -> FastAPI:
    app = FastAPI(
        title=Config.SERVICE_NAME,
        debug=Config.DEBUG,
        description=Config.DESCRIPTION,
        version=VERSION,
        lifespan=lifespan,
    )
    setup_middleware(app)
    PATH_PREFIX = "/stenagrafist" + Config.API_V1_STR
    app.add_route("/metrics", metrics)
    app.include_router(api.router, prefix=PATH_PREFIX)
    return app


app = create_app()
