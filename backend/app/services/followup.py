import json
import logging
import re

from app.core.config import settings
from app.services.graph.state import ChatState
from app.services.llm import chat_completion

logger = logging.getLogger("app.services.followup")

# Prefixed onto every follow-up message so later turns can recognize it in
# chat_history without any extra state — this is the only signal we have for
# "how many unsuccessful attempts in a row", since the graph is stateless
# across requests and history is round-tripped by the frontend.
_FOLLOWUP_PREFIX = (
    "I couldn't find a fully confident answer to that yet. Here are some "
    "related questions I can help with:"
)

_MIN_SUGGESTIONS = 3
_MAX_SUGGESTIONS = 5

_SYSTEM_PROMPT = (
    "A user asked a question on the TEF (Tony Elumelu Foundation) platform, but "
    "the retrieved knowledge base context wasn't confident/complete enough to "
    "answer directly. Do not answer the question and do not invent facts.\n\n"
    f"Suggest {_MIN_SUGGESTIONS}-{_MAX_SUGGESTIONS} follow-up questions that:\n"
    "- Are specific to the TEF platform's actual features and workflows (e.g. "
    "mentorship pairing, M&E enumerator/reviewer roles, audit processes, "
    "pitching, account/role management) — never generic chatbot filler like "
    "'can you clarify?' or 'what do you mean?'.\n"
    "- Are each answerable from the context excerpts and/or topic given below; "
    "do not invent a question about something not grounded in them.\n"
    "- Stay closely related to the user's original topic, helping narrow down "
    "what they're looking for.\n"
    "- Are phrased as complete, standalone questions a user could click and "
    "send as-is — no 'or', no placeholders, no leading numbering/bullets.\n\n"
    "Respond with ONLY a JSON array of question strings, nothing else. "
    'Example JSON output: ["How do I reset my password?", "How does a Mentor '
    'Admin pair an entrepreneur with a mentor?"]'
)


def _build_context(state: ChatState) -> str:
    hits = state.get("kb_hits") or state.get("faq_hits") or []
    return "\n\n".join(h["document"] for h in hits[:3])


_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)
_LEADING_MARKER_RE = re.compile(r"^[\-\*\d.\)]+\s*")


def _parse_suggestions(raw: str) -> list[str]:
    match = _JSON_ARRAY_RE.search(raw)
    if match:
        try:
            parsed = json.loads(match.group())
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            questions = [str(q).strip() for q in parsed if str(q).strip()]
            if questions:
                return questions[:_MAX_SUGGESTIONS]

    # Models sometimes ignore the "JSON only" instruction and fall back to a
    # bullet/numbered list despite it; salvage that instead of returning nothing.
    logger.warning("Followup: No JSON array found in LLM response '%s'. Falling back to line parsing.", raw)
    lines = [_LEADING_MARKER_RE.sub("", line).strip() for line in raw.splitlines()]
    return [line for line in lines if line][:_MAX_SUGGESTIONS]


def suggest_followups(state: ChatState) -> dict:
    context = _build_context(state)
    user_prompt = f"User's question: {state['refined_query']}\nTopic: {state.get('intent') or 'general'}"
    if context:
        user_prompt += f"\n\nRelated context excerpts (ground the suggested questions in these):\n{context}"
    else:
        user_prompt += "\n\nNo related context excerpts were retrieved; ground suggestions in the topic only."

    raw = chat_completion(_SYSTEM_PROMPT, user_prompt).strip()
    suggestions = _parse_suggestions(raw)

    logger.info(
        "Followup: Suggested %d clarifying question(s) for '%s' (intent=%s)",
        len(suggestions), state["refined_query"], state.get("intent"),
    )
    return {
        "answer": _FOLLOWUP_PREFIX,
        "escalated": False,
        "sources": [],
        "followup_suggestions": suggestions,
    }


def _consecutive_unsuccessful_attempts(chat_history: list[dict]) -> int:
    count = 0
    for msg in reversed(chat_history or []):
        if msg.get("role") != "assistant":
            continue
        if _FOLLOWUP_PREFIX in (msg.get("content") or ""):
            count += 1
        else:
            break
    return count


def escalation_decision_router(state: ChatState) -> str:
    attempts = _consecutive_unsuccessful_attempts(state.get("chat_history") or [])
    if attempts >= settings.max_followup_attempts:
        return "escalate"
    return "clarify"
