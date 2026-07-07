import json
import logging
from pathlib import Path

from app.core.config import settings
from app.services.llm import chat_completion

logger = logging.getLogger("app.services.intent_extractor")

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
        "Classify the user's message into exactly one of these categories: "
        f"{', '.join(categories)}. If nothing else fits, use '{_FALLBACK_CATEGORY}'. "
        "Also extract any clear entities. "
        "Respond with ONLY a JSON object of the exact shape "
        '{"intent": "<one_of_the_categories_above>", "entities": {"<name>": "<value>", ...}}. '
        "If there are no clear entities, use an empty object. Do not add commentary."
    )


def extract_intent_entities(message: str) -> tuple[str, dict[str, str]]:
    categories = list_categories()
    logger.info("IntentExtractor: Requesting intent/entity extraction from LLM...")
    raw = chat_completion(_build_system_prompt(categories), message).strip()
    try:
        # Tolerate accidental markdown code fences around the JSON.
        cleaned = raw.strip("`").removeprefix("json").strip() if raw.startswith("```") else raw
        parsed = json.loads(cleaned)
        intent = str(parsed.get("intent") or "").strip()
        if intent not in categories:
            logger.warning("IntentExtractor: intent '%s' not in known categories %s. Falling back to '%s'.", intent, categories, _FALLBACK_CATEGORY)
            intent = _FALLBACK_CATEGORY
        entities = parsed.get("entities") or {}
        if not isinstance(entities, dict):
            entities = {}
        entities = {str(k): str(v) for k, v in entities.items()}
        logger.info("IntentExtractor: intent='%s' entities=%s", intent, entities)
        return intent, entities
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        logger.warning("IntentExtractor: Failed to parse LLM response '%s' (%s). Defaulting to '%s'.", raw, e, _FALLBACK_CATEGORY)
        return _FALLBACK_CATEGORY, {}
