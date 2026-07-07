import logging
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.pipeline import handle_message

logger = logging.getLogger("app.api.routes.chat")
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    confidence: float | None = None
    escalated: bool
    answered_by: Literal["faq", "kb"] | None = None
    support_email: str | None = None
    support_phone: str | None = None
    sources: list[str] = []


@router.post("", response_model=ChatResponse)
def post_chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    logger.info("Received POST /chat request. User ID: %s, Message length: %d characters", request.user_id, len(request.message))
    try:
        result = handle_message(db, request.user_id, request.message)
        logger.info(
            "Successfully processed message for User ID: %s. answered_by=%s confidence=%s escalated=%s",
            request.user_id, result.answered_by, result.confidence, result.escalated,
        )
        return ChatResponse(
            answer=result.answer,
            confidence=result.confidence,
            escalated=result.escalated,
            answered_by=result.answered_by,
            support_email=settings.support_email if result.escalated else None,
            support_phone=settings.support_phone if result.escalated else None,
            sources=result.sources,
        )
    except Exception as e:
        logger.error("Exception occurred while handling chat message for User ID: %s: %s", request.user_id, str(e), exc_info=True)
        raise e
