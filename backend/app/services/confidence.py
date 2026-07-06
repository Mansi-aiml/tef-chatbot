import logging
from app.services.llm import chat_completion

logger = logging.getLogger("app.services.confidence")

_SYSTEM_PROMPT = (
    "Rate how confident you are that the given answer correctly and fully "
    "resolves the given question, on a scale from 0.0 (not confident) to "
    "1.0 (fully confident). Respond with only the number."
)


def score_confidence(query: str, answer: str) -> float:
    logger.info("ConfidenceGate: Requesting confidence score from LLM...")
    user_prompt = f"Question: {query}\n\nAnswer: {answer}"
    raw = chat_completion(_SYSTEM_PROMPT, user_prompt).strip()
    logger.info("ConfidenceGate: Raw LLM response: '%s'", raw)
    try:
        score = max(0.0, min(1.0, float(raw)))
        logger.info("ConfidenceGate: Parsed score: %.2f", score)
        return score
    except ValueError:
        logger.warning("ConfidenceGate: Failed to parse float from LLM response '%s'. Defaulting to 0.0.", raw)
        return 0.0
