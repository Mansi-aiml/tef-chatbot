from sqlalchemy.orm import Session

from app.db.models import SupportTicket


def create_support_ticket(db: Session, user_id: str, query: str, draft_answer: str, confidence: float) -> SupportTicket:
    ticket = SupportTicket(
        user_id=user_id,
        query=query,
        draft_answer=draft_answer,
        confidence=confidence,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
