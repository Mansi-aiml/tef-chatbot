import logging

from app.core.config import settings
from app.services.graph.state import ChatState
from app.services.llm import chat_completion

logger = logging.getLogger("app.services.confidence")

_SYSTEM_PROMPT = (
    "Rate, from 0.0 (not at all) to 1.0 (completely), how likely the given context "
    "excerpts are to fully and accurately answer the given question. "
    "Respond with only the number."
)


def _retrieval_score(hits: list[dict]) -> float:
    # Cosine distance is bounded [0, 2]; convert to a [0, 1] similarity score.
    similarities = [max(0.0, min(1.0, 1 - (h["distance"] / 2))) for h in hits]
    return sum(similarities) / len(similarities) if similarities else 0.0


def _llm_context_score(query: str, hits: list[dict]) -> float:
    context = "\n\n".join(h["document"] for h in hits)
    user_prompt = f"Question: {query}\n\nContext:\n{context}"
    raw = chat_completion(_SYSTEM_PROMPT, user_prompt).strip()
    try:
        return max(0.0, min(1.0, float(raw)))
    except ValueError:
        logger.warning("Confidence: Failed to parse float from LLM response '%s'. Defaulting to 0.0.", raw)
        return 0.0


def score_confidence(state: ChatState) -> dict:
    hits = state.get("kb_hits", [])
    retrieval_score = _retrieval_score(hits)
    llm_score = _llm_context_score(state["refined_query"], hits)

    weight = settings.confidence_retrieval_weight
    confidence = weight * retrieval_score + (1 - weight) * llm_score
    logger.info(
        "Confidence: retrieval=%.2f llm=%.2f combined=%.2f (threshold=%.2f)",
        retrieval_score, llm_score, confidence, settings.confidence_threshold,
    )
    return {"confidence": confidence}


def confidence_router(state: ChatState) -> str:
    if (state.get("confidence") or 0.0) >= settings.confidence_threshold:
        return "pass"
    return "fail"
