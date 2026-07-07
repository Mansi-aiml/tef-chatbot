from app.services.graph.state import ChatState
from app.services.vectorstore.chroma_client import RetrievedChunk, query_collection


def reformulate(state: ChatState) -> str:
    """Second-attempt query: fold intent/entities into the refined query so a
    retry can surface matches a plain semantic search on the first pass missed."""
    entity_values = " ".join(state.get("entities", {}).values())
    intent = state.get("intent", "")
    parts = [p for p in (intent, entity_values, state["refined_query"]) if p]
    return " ".join(parts)


def search_with_retry(
    collection,
    state: ChatState,
    attempt: int,
    base_threshold: float,
    base_top_k: int,
    loosen_factor: float,
) -> tuple[str, list[RetrievedChunk]]:
    """Run one attempt of a layer's semantic search. Attempt 1 uses the refined
    query at the configured threshold; attempt 2+ reformulates the query and
    loosens the threshold/widens top_k to give the retry a real chance."""
    if attempt <= 1:
        query = state["refined_query"]
        threshold = base_threshold
        top_k = base_top_k
    else:
        query = reformulate(state)
        threshold = base_threshold * loosen_factor
        top_k = base_top_k + 2

    hits = query_collection(collection, query, top_k)
    hits = [h for h in hits if h["distance"] <= threshold]
    return query, hits
