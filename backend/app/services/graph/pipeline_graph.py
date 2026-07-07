from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.services.graph.state import ChatState
from app.services.intent_extractor import extract_intent_entities
from app.services.retrieval.confidence import confidence_router, score_confidence
from app.services.retrieval.faq_layer import faq_router, faq_search
from app.services.retrieval.kb_layer import kb_router, kb_search
from app.services.query_refiner import refine_query
from app.services.support import make_escalate_node
from app.services.synthesis import synthesize


def _refine_node(state: ChatState) -> dict:
    return {"refined_query": refine_query(state["raw_message"])}


def _intent_node(state: ChatState) -> dict:
    intent, entities = extract_intent_entities(state["refined_query"])
    return {"intent": intent, "entities": entities}


def build_graph(db: Session):
    """Compiled per-request so the escalate node can close over this request's
    DB session — the graph itself completes within a single request/response
    cycle, so there's no need for LangGraph checkpointing/persistence here."""
    graph = StateGraph(ChatState)

    graph.add_node("refine", _refine_node)
    graph.add_node("extract_intent_entities", _intent_node)
    graph.add_node("faq_search", faq_search)
    graph.add_node("kb_search", kb_search)
    graph.add_node("score_confidence", score_confidence)
    graph.add_node("synthesize", synthesize)
    graph.add_node("escalate", make_escalate_node(db))

    graph.set_entry_point("refine")
    graph.add_edge("refine", "extract_intent_entities")
    graph.add_edge("extract_intent_entities", "faq_search")

    graph.add_conditional_edges(
        "faq_search",
        faq_router,
        {"found": "synthesize", "retry": "faq_search", "give_up": "kb_search"},
    )
    graph.add_conditional_edges(
        "kb_search",
        kb_router,
        {"found": "score_confidence", "retry": "kb_search", "give_up": "escalate"},
    )
    graph.add_conditional_edges(
        "score_confidence",
        confidence_router,
        {"pass": "synthesize", "fail": "escalate"},
    )

    graph.add_edge("synthesize", END)
    graph.add_edge("escalate", END)

    return graph.compile()
