from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.errors import http_exception_handler, validation_exception_handler
from api.routers import auth, members, payments, rooms, settlements
from config import CORS_ORIGINS

app = FastAPI(title="Rexab API")

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
