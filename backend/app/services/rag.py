from app.services.llm import chat_completion
from app.vectorstore.chroma_client import query_knowledge_base

_SYSTEM_PROMPT = (
    "Answer the user's question using only the provided context. "
    "If the context does not contain the answer, say you don't know."
)


def answer_from_knowledge_base(query: str) -> str:
    results = query_knowledge_base(query)
    context = "\n\n".join(r["document"] for r in results)
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
    return chat_completion(_SYSTEM_PROMPT, user_prompt)
