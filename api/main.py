from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.errors import http_exception_handler, validation_exception_handler
from api.routers import auth, dashboard, members, payments, rooms, settlements
from config import CORS_ORIGINS
from database.init_db import init_db
from logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # The bot's entrypoint also calls this; the API needs it too so it
    # can run standalone without the bot ever having started first.
    await init_db()
    yield


app = FastAPI(title="Rexab API", lifespan=lifespan)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(
    RequestValidationError, validation_exception_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(members.router)
app.include_router(payments.router)
app.include_router(settlements.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
