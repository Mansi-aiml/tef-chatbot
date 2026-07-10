# TEF Chatbot

A chatbot that answers user queries using FAQs and a knowledge base (RAG), orchestrated as a LangGraph pipeline. Low-confidence answers are escalated to a human support agent instead of being sent to the user.

## Architecture / request flow

1. User sends a message from the frontend.
2. **Refine + intent/entity extraction**: a single LLM call rewrites the raw message into a clear, self-contained query (typo/spelling correction) and tags it with an intent label and any entities.
3. **FAQ layer** (Layer 1): semantic search against a dedicated FAQ Chroma collection, files stored under `backend/faq/`. Retried up to 2 attempts (query reformulation + loosened threshold on the 2nd try). On a hit, skips straight to synthesis — **FAQ answers are not confidence-gated**.
4. **Knowledge base layer** (Layer 2, reached only if FAQ misses both attempts): semantic search against the KB Chroma collection, files under `backend/knowledgebase/`. Also retried up to 2 attempts.
5. **Confidence gate** (KB-only): a hybrid of retrieval similarity + an LLM context-sufficiency score. This is the *only* point in the pipeline where confidence is scored.
6. **Synthesis**: on an FAQ hit or a passing KB confidence score, the top-k retrieved chunks + refined query are sent to the LLM to produce the final answer (one shared node for both success paths).
7. **Escalation** (Layer 3, fallback): reached if neither layer finds a match, or KB confidence is below threshold. Creates a `SupportTicket` row and returns a message with the configured support email/phone.

When working on any stage of this pipeline, preserve this routing order (FAQ → knowledge base → escalation), the 2-attempt retry on each of the FAQ/KB layers, and the fact that confidence scoring only gates the KB layer — never send a low-confidence KB answer directly to the user, and never gate FAQ answers on confidence.

## Tech stack

- Frontend: React (Vite) — `frontend/`
- Backend: Python (FastAPI) — `backend/`
- Orchestration: LangGraph (`backend/app/services/graph/`) — the pipeline is a `StateGraph` with retry loops (FAQ/KB) and conditional edges (confidence gate, escalation). LangChain is used only inside the ingestion script for document loaders/text splitting, not for the graph itself.
- LLM: Groq (`backend/app/services/llm.py`)
- Vector DB: Chroma, persisted to `backend/chroma_data/`, two collections (`faqs`, `knowledge_base`) via `backend/app/services/vectorstore/chroma_client.py`. Embeddings are Chroma's bundled local default (no external embeddings API).
- Database: PostgreSQL via SQLAlchemy (`backend/app/db/`) — used only for `SupportTicket` rows now (FAQs moved to files, see below).

## Code layout

- `backend/app/api/routes/chat.py` — the single `POST /chat` endpoint
- `backend/app/services/pipeline.py` — builds the LangGraph, invokes it, maps the result to a `ChatResult`
- `backend/app/services/graph/state.py` — the shared `ChatState` TypedDict schema
- `backend/app/services/graph/pipeline_graph.py` — graph wiring (nodes + conditional edges)
- `backend/app/services/query_understanding.py` — combined refine + intent/entity extraction node (single LLM call), constrained to the category folders under `backend/faq/`
- `backend/app/services/retrieval/faq_layer.py`, `kb_layer.py` — the two retrieval layers (search node + router fn each), scoped to the classified intent's category on the first attempt
- `backend/app/services/retrieval/shared.py` — shared query-with-retry / query-reformulation helpers used by both layers
- `backend/app/services/retrieval/confidence.py` — KB-only confidence gate (retrieval similarity + LLM context-sufficiency hybrid)
- `backend/app/services/synthesis.py` — shared answer-synthesis node (used by both FAQ and KB success paths)
- `backend/app/services/support.py` — support ticket creation + escalation node
- `backend/app/db/models.py` — `SupportTicket` table
- `backend/faq/<Category>/*.json` — FAQ content, one JSON array of `{question, answer}` per file, category folders mirror `backend/knowledgebase/`
- `backend/knowledgebase/<Category>/...` — knowledge-base source documents (.docx/.pdf/.txt/.md)
- `backend/scripts/ingest.py` — ingestion script for both collections: `python -m scripts.ingest --collection knowledge_base --path ./knowledgebase` / `--collection faq --path ./faq`

`backend/faq/` currently only has placeholder/general FAQ content (`Common/general.json`) plus empty per-category `readme.md` markers — real FAQ authoring per category is an ongoing content task, not a code task. After adding/editing a `.json` file there, re-run the `faq` ingestion command above (add `--reset` first if you edited existing entries rather than just adding new ones).

## Conventions

- Backend: run from `backend/` with a venv (`python3 -m venv .venv`), deps in `requirements.txt`, config via `.env` (see `.env.example`) loaded through `app/core/config.py` (pydantic-settings).
- Frontend: standard Vite React app in `frontend/`, run with `npm install && npm run dev`.
- Secrets (`GROQ_API_KEY`, `DATABASE_URL`) live in `backend/.env`, which is gitignored — never commit it.
