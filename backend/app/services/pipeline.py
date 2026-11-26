import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services.graph.pipeline_graph import build_graph
from app.services.language import normalize_language
from app.services.llm import estimate_cost, track_usage

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
    token_usage: dict | None = None


_MAX_HISTORY_TURNS = 10


def _step_cost(s: dict) -> float:
    return estimate_cost(s["prompt_tokens"], s["completion_tokens"])


def handle_message(
    db: Session,
    user_id: str,
    message: str,
    history: list[dict[str, str]] | None = None,
    language: str | None = None,
) -> ChatResult:
    logger.info("Pipeline: Handling message for User %s. Message preview: '%s'", user_id, message[:60])

    graph = build_graph()
    with track_usage() as usage:
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

    breakdown = "\n".join(
        f"    {step:<22} calls={s['calls']:<2} prompt={s['prompt_tokens']:<6} completion={s['completion_tokens']:<5} "
        f"total={s['total_tokens']:<6} cost=${_step_cost(s):.6f}"
        for step, s in usage.by_step.items()
    )
    logger.info(
        "Pipeline: Token usage for User %s -> calls=%d prompt=%d completion=%d total=%d tokens | cost=$%.6f\n%s",
        user_id, usage.calls, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens, usage.cost_usd, breakdown,
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
        token_usage=usage.to_dict(),
    )
