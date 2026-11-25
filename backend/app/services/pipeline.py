import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services.graph.pipeline_graph import build_graph
from app.services.language import normalize_language

logger = logging.getLogger("app.services.pipeline")


@dataclass
class ChatResult:
    answer: str
    confidence: float | None
    escalated: bool
    answered_by: str | None = None
    out_of_scope: bool = False
    sources: list[str] = field(default_factory=list)
    followup_suggestions: list[str] = field(default_factory=list)


_MAX_HISTORY_TURNS = 10


def handle_message(
    db: Session,
    user_id: str,
    message: str,
    history: list[dict[str, str]] | None = None,
    language: str | None = None,
) -> ChatResult:
    logger.info("Pipeline: Handling message for User %s. Message preview: '%s'", user_id, message[:60])

    graph = build_graph()
    result = graph.invoke(
        {
            "user_id": user_id,
            "raw_message": message,
            "chat_history": (history or [])[-_MAX_HISTORY_TURNS:],
            "language": normalize_language(language),
            "faq_attempt": 0,
            "kb_attempt": 0,
        }
    )

    logger.info(
        "Pipeline: Completed. answered_by=%s confidence=%s escalated=%s",
        result.get("answered_by"), result.get("confidence"), result.get("escalated"),
    )

    return ChatResult(
        answer=result.get("answer") or "",
        confidence=result.get("confidence"),
        escalated=bool(result.get("escalated")),
        answered_by=result.get("answered_by"),
        out_of_scope=bool(result.get("out_of_scope")),
        sources=result.get("sources", []),
        followup_suggestions=result.get("followup_suggestions", []),
    )
