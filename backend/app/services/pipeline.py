from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import rag, support, user_data
from app.services.confidence import score_confidence
from app.services.faq import lookup_faq
from app.services.router import QueryType, classify_query


@dataclass
class ChatResult:
    answer: str
    confidence: float
    escalated: bool


def handle_message(db: Session, user_id: str, message: str) -> ChatResult:
    query_type = classify_query(message)

    answer: str | None = None

    if query_type == QueryType.FAQ:
        faq = lookup_faq(db, message)
        if faq is not None:
            answer = faq.answer

    elif query_type == QueryType.USER_DATA:
        answer = user_data.lookup_user_data(user_id, message)

    if answer is None:
        answer = rag.answer_from_knowledge_base(message)

    confidence = score_confidence(message, answer)

    if confidence < settings.confidence_threshold:
        support.create_support_ticket(db, user_id, message, answer, confidence)
        return ChatResult(
            answer="Thanks for reaching out — I've escalated this to our support team, who will follow up with you shortly.",
            confidence=confidence,
            escalated=True,
        )

    return ChatResult(answer=answer, confidence=confidence, escalated=False)
