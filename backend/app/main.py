import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.core.config import settings
from app.db.session import Base, engine
from app.db import models  # noqa: F401 (registers SupportTicket on Base.metadata)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")
logger.info("Initializing TEF Chatbot backend application...")

app = FastAPI(title="TEF Chatbot")

Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    logger.info("Received request on /health endpoint")
    return {"status": "ok"}
