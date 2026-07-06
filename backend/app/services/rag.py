import logging
from app.services.llm import chat_completion
from app.vectorstore.chroma_client import query_knowledge_base

logger = logging.getLogger("app.services.rag")

_SYSTEM_PROMPT = (
    "Answer the user's question using only the provided context. "
    "If the context does not contain the answer, say you don't know."
)


def answer_from_knowledge_base(query: str) -> str:
    logger.info("RAG: Querying Chroma knowledge base...")
    results = query_knowledge_base(query)
    logger.info("RAG: Retrieved %d context document(s) from vector store", len(results))
    
    context = "\n\n".join(r["document"] for r in results)
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
    
    logger.info("RAG: Requesting LLM response generation with context...")
    response = chat_completion(_SYSTEM_PROMPT, user_prompt)
    logger.info("RAG: LLM response generation completed successfully")
    return response
