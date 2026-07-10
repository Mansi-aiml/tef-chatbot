import json
import logging
from pathlib import Path

from app.core.config import settings
from app.services.llm import chat_completion

logger = logging.getLogger("app.services.query_understanding")

# "common" is the catch-all bucket (general/account-support FAQs live there),
# so it's always a valid fallback even if the folder listing below is empty.
_FALLBACK_CATEGORY = "common"


def list_categories() -> list[str]:
    """Category labels the FAQ/KB layers can filter on, derived from the
    folder structure under faq_data_dir rather than hardcoded, so new
    categories added on disk are picked up without a code change."""
    root = Path(settings.faq_data_dir)
    if not root.is_dir():
        return [_FALLBACK_CATEGORY]
    categories = sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    return categories or [_FALLBACK_CATEGORY]


def _build_system_prompt(categories: list[str]) -> str:
    return (
        "You will be given a raw user message. Do two things with it:\n"
        "1. Rewrite it into a clear, unambiguous, self-contained query: expand "
        "abbreviations, fix typos, and make any implicit intent explicit, but do "
        "not add information the user didn't imply.\n"
        "2. Classify the ORIGINAL message into exactly one of these categories: "
        f"{', '.join(categories)}. If nothing else fits, use '{_FALLBACK_CATEGORY}'. "
        "Also extract any clear entities.\n"
        "Respond with ONLY a JSON object of the exact shape "
        '{"refined_query": "<rewritten query>", "intent": "<one_of_the_categories_above>", '
        '"entities": {"<name>": "<value>", ...}}. '
        "If there are no clear entities, use an empty object. Do not add commentary."
    )


def refine_and_classify(message: str) -> tuple[str, str, dict[str, str]]:
    """Single LLM call that both rewrites the raw message into a refined query
    and classifies it into an intent category with entities, replacing what
    used to be two sequential LLM round-trips (refine, then extract)."""
    categories = list_categories()
    logger.info("QueryUnderstanding: Requesting refined query + intent/entities from LLM...")
    raw = chat_completion(_build_system_prompt(categories), message).strip()
    try:
        # Tolerate accidental markdown code fences around the JSON.
        cleaned = raw.strip("`").removeprefix("json").strip() if raw.startswith("```") else raw
        parsed = json.loads(cleaned)

        refined_query = str(parsed.get("refined_query") or "").strip() or message

        intent = str(parsed.get("intent") or "").strip()
        if intent not in categories:
            logger.warning("QueryUnderstanding: intent '%s' not in known categories %s. Falling back to '%s'.", intent, categories, _FALLBACK_CATEGORY)
            intent = _FALLBACK_CATEGORY

        entities = parsed.get("entities") or {}
        if not isinstance(entities, dict):
            entities = {}
        entities = {str(k): str(v) for k, v in entities.items()}

        logger.info("QueryUnderstanding: refined_query='%s' intent='%s' entities=%s", refined_query, intent, entities)
        return refined_query, intent, entities
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        logger.warning("QueryUnderstanding: Failed to parse LLM response '%s' (%s). Falling back to raw message / '%s'.", raw, e, _FALLBACK_CATEGORY)
        return message, _FALLBACK_CATEGORY, {}
