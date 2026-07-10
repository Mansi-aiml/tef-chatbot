import logging

from app.services.graph.state import ChatState
from app.services.llm import chat_completion

logger = logging.getLogger("app.services.synthesis")

_SYSTEM_PROMPT = (
    "Answer the user's question using only the provided context excerpts. "
    "Write a clear, direct, well-formatted answer for the end user. "
    "If the context does not fully cover the question, answer with what it does "
    "cover and note what's missing rather than refusing outright."
)


def synthesize(state: ChatState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    context = "\n\n".join(c["document"] for c in chunks)
    user_prompt = f"Context:\n{context}\n\nQuestion: {state['refined_query']}"

    logger.info("Synthesis: Generating final answer from %d chunk(s), answered_by=%s", len(chunks), state.get("answered_by"))
    answer = chat_completion(_SYSTEM_PROMPT, user_prompt)

    sources = sorted({c["metadata"].get("source", "") for c in chunks if c["metadata"].get("source")})
    return {"answer": answer, "escalated": False, "sources": sources}

