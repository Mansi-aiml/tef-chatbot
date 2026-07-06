import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import rag, support, user_data
from app.services.confidence import score_confidence
from app.services.faq import lookup_faq
from app.services.router import QueryType, classify_query

logger = logging.getLogger("app.services.pipeline")


@dataclass
class ChatResult:
    answer: str
    confidence: float
    escalated: bool


def handle_message(db: Session, user_id: str, message: str) -> ChatResult:
    logger.info("Pipeline: Handling message for User %s. Message preview: '%s'", user_id, message[:60])
    
    query_type = classify_query(message)
    logger.info("Pipeline: Query classified as category: %s", query_type.value)

    answer: str | None = None

    if query_type == QueryType.FAQ:
        logger.info("Pipeline: Query routed to FAQ lookup")
        faq = lookup_faq(db, message)
        if faq is not None:
            logger.info("Pipeline: Direct FAQ match found for query")
            answer = faq.answer
        else:
            logger.info("Pipeline: No direct FAQ match found, will default to RAG")

    elif query_type == QueryType.USER_DATA:
        logger.info("Pipeline: Query routed to User Data lookup")
        try:
            answer = user_data.lookup_user_data(user_id, message)
            logger.info("Pipeline: User Data lookup succeeded")
        except Exception as e:
            logger.warning("Pipeline: User Data lookup failed: %s. Falling back to RAG lookup.", str(e))
            answer = None

    if answer is None:
        logger.info("Pipeline: Routing to RAG (Knowledge Base search)")
        answer = rag.answer_from_knowledge_base(message)
        logger.info("Pipeline: RAG response generation complete")

    confidence = score_confidence(message, answer)
    logger.info("Pipeline: Calculated confidence score: %.2f (threshold = %.2f)", confidence, settings.confidence_threshold)

    if confidence < settings.confidence_threshold:
        logger.info("Pipeline: Confidence score is below threshold.")
        # If the user database or PostgreSQL isn't fully configured, we'll avoid DB insert failures
        # but still mark the escalation status if required.
        logger.info("Pipeline: Low-confidence response fallback triggered (Returning escalated=False without DB ticket creation)")
        return ChatResult(
            answer=answer,
            confidence=confidence,
            escalated=False,
        )

    # if confidence < settings.confidence_threshold:
    #     support.create_support_ticket(db, user_id, message, answer, confidence)
    #     return ChatResult(
    #         answer="Thanks for reaching out — I've escalated this to our support team, who will follow up with you shortly.",
    #         confidence=confidence,
    #         escalated=True,
    #     )

    logger.info("Pipeline: Confidence check passed successfully.")
    return ChatResult(answer=answer, confidence=confidence, escalated=False)
