import json
import logging

from sqlalchemy.orm import Session

from app.db.models import SupportTicket
from app.services.graph.state import ChatState
from app.services.language import out_of_scope_message

logger = logging.getLogger("app.services.support")


def create_support_ticket(
    db: Session,
    user_id: str,
    query: str,
    draft_answer: str | None,
    confidence: float,
    intent: str | None,
    entities: dict[str, str] | None,
    escalation_reason: str | None,
) -> SupportTicket:
    ticket = SupportTicket(
        user_id=user_id,
        query=query,
        draft_answer=draft_answer,
        confidence=confidence,
        intent=intent,
        entities_json=json.dumps(entities or {}),
        escalation_reason=escalation_reason,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    logger.info("Support: Created ticket %s (reason=%s)", ticket.id, escalation_reason)
    return ticket


def out_of_scope(state: ChatState) -> dict:
    """Final fallback when neither layer can answer and follow-ups are exhausted.

    Deliberately does NOT create a support ticket — replying with a warm
    out-of-scope message is friendlier than escalating on the user's behalf.
    The frontend then shows its feedback prompt, where the user can opt in to
    a ticket (POST /chat/feedback/ticket) if they still need help.
    """
    reason = "low_confidence" if state.get("kb_hits") else "not_found"
    logger.info("Support: Out of scope (reason=%s) for '%s'", reason, state.get("refined_query"))
    return {
        "answer": out_of_scope_message(state.get("language")),
        "escalated": False,
        "out_of_scope": True,
        "followup_suggestions": [],
        "sources": [],
    }
