import logging

from app.services.llm import chat_completion

logger = logging.getLogger("app.services.query_refiner")

_SYSTEM_PROMPT = (
    "Rewrite the user's message into a clear, unambiguous, self-contained query. "
    "Expand abbreviations, fix typos, and make any implicit intent explicit, but "
    "do not add information the user didn't imply. Respond with only the rewritten "
    "query and nothing else."
)


def refine_query(message: str) -> str:
    logger.info("QueryRefiner: Requesting refined query from LLM...")
    raw = chat_completion(_SYSTEM_PROMPT, message).strip()
    if not raw:
        logger.warning("QueryRefiner: LLM returned empty response. Falling back to original message.")
        return message
    logger.info("QueryRefiner: Refined query: '%s'", raw)
    return raw
