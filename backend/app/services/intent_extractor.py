import json
import logging

from app.services.llm import chat_completion

logger = logging.getLogger("app.services.intent_extractor")

_SYSTEM_PROMPT = (
    "Classify the user's message and extract entities. Consider intents such as "
    "audit, lms, mentorship, monitoring_evaluation, pitching, entrepreneur_onboarding, "
    "account_support, or other/general topics if none of those fit. "
    "Respond with ONLY a JSON object of the exact shape "
    '{"intent": "<short_snake_case_label>", "entities": {"<name>": "<value>", ...}}. '
    "If there are no clear entities, use an empty object. Do not add commentary."
)


def extract_intent_entities(message: str) -> tuple[str, dict[str, str]]:
    logger.info("IntentExtractor: Requesting intent/entity extraction from LLM...")
    raw = chat_completion(_SYSTEM_PROMPT, message).strip()
    try:
        # Tolerate accidental markdown code fences around the JSON.
        cleaned = raw.strip("`").removeprefix("json").strip() if raw.startswith("```") else raw
        parsed = json.loads(cleaned)
        intent = str(parsed.get("intent") or "unknown")
        entities = parsed.get("entities") or {}
        if not isinstance(entities, dict):
            entities = {}
        entities = {str(k): str(v) for k, v in entities.items()}
        logger.info("IntentExtractor: intent='%s' entities=%s", intent, entities)
        return intent, entities
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        logger.warning("IntentExtractor: Failed to parse LLM response '%s' (%s). Defaulting to unknown.", raw, e)
        return "unknown", {}
