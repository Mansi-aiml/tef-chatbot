from enum import Enum

from app.services.llm import chat_completion

_SYSTEM_PROMPT = (
    "Classify the user's message into exactly one category: "
    "'faq' for general questions answerable from a static FAQ, "
    "'user_data' for questions about the specific user's own account/data, "
    "or 'rag' for anything else that needs a knowledge base search. "
    "Respond with only the category word."
)


class QueryType(str, Enum):
    FAQ = "faq"
    USER_DATA = "user_data"
    RAG = "rag"


def classify_query(message: str) -> QueryType:
    raw = chat_completion(_SYSTEM_PROMPT, message).strip().lower()
    try:
        return QueryType(raw)
    except ValueError:
        return QueryType.RAG
