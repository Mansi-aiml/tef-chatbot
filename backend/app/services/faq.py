import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FAQ

logger = logging.getLogger("app.services.faq")


def lookup_faq(db: Session, query: str) -> FAQ | None:
    """Direct-match lookup against the FAQ table.

    TODO: replace exact match with fuzzy/embedding-based matching once
    the FAQ table has real content.
    """
    logger.info("FAQ: Querying FAQ table for: '%s'", query)
    stmt = select(FAQ).where(FAQ.question.ilike(query))
    result = db.execute(stmt).scalar_one_or_none()
    if result is not None:
        logger.info("FAQ: Match found (ID: %s)", result.id)
    else:
        logger.info("FAQ: No exact match found")
    return result
