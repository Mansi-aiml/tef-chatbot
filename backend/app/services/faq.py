from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FAQ


def lookup_faq(db: Session, query: str) -> FAQ | None:
    """Direct-match lookup against the FAQ table.

    TODO: replace exact match with fuzzy/embedding-based matching once
    the FAQ table has real content.
    """
    stmt = select(FAQ).where(FAQ.question.ilike(query))
    return db.execute(stmt).scalar_one_or_none()
