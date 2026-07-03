from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.pipeline import handle_message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    escalated: bool


@router.post("", response_model=ChatResponse)
def post_chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    result = handle_message(db, request.user_id, request.message)
    return ChatResponse(answer=result.answer, confidence=result.confidence, escalated=result.escalated)
