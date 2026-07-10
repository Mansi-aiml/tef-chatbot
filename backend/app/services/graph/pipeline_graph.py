from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.services.graph.state import ChatState
from app.services.query_understanding import refine_and_classify
from app.services.retrieval.confidence import confidence_router, score_confidence
from app.services.retrieval.faq_layer import faq_router, faq_search
from app.services.retrieval.kb_layer import kb_router, kb_search
from app.services.support import make_escalate_node
from app.services.synthesis import synthesize


def _refine_and_classify_node(state: ChatState) -> dict:
    refined_query, intent, entities = refine_and_classify(state["raw_message"])
    return {"refined_query": refined_query, "intent": intent, "entities": entities}


def build_graph(db: Session):
    """Compiled per-request so the escalate node can close over this request's
    DB session — the graph itself completes within a single request/response
    cycle, so there's no need for LangGraph checkpointing/persistence here."""
    graph = StateGraph(ChatState)

    graph.add_node("refine_and_classify", _refine_and_classify_node)
    graph.add_node("faq_search", faq_search)
    graph.add_node("kb_search", kb_search)
    graph.add_node("score_confidence", score_confidence)
    graph.add_node("synthesize", synthesize)
    graph.add_node("escalate", make_escalate_node(db))

    graph.set_entry_point("refine_and_classify")
    graph.add_edge("refine_and_classify", "faq_search")

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
