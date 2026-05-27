from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.services import anomalies


@asynccontextmanager
async def lifespan(app: FastAPI):
    anomalies.warm_cache()
    yield


app = FastAPI(title="Canva for Data POC", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
