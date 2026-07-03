# TEF Chatbot

A chatbot that answers user queries using FAQs, user data, and a knowledge base (RAG). Low-confidence answers are escalated to support instead of being sent to the user.

## Architecture / request flow

1. User sends a message from the frontend.
2. The query is refined, classified, and routed.
3. Depending on the query type, it looks up one of:
   - FAQ (direct match)
   - User data (via backend API)
   - Knowledge base (vector search / RAG)
4. If no direct FAQ answer is found, it falls back to RAG search.
5. A response is generated from the retrieved info.
6. Confidence check on the generated response:
   - High confidence → answer sent to user
   - Low confidence → support ticket created + user notified

When working on any stage of this pipeline, preserve this routing order (FAQ → user data → RAG fallback) and the confidence-gate before a response reaches the user — never send a low-confidence answer directly to the user.

## Tech stack

- Frontend: React (Vite) — `frontend/`
- Backend: Python (FastAPI) — `backend/`
- LLM: Groq (`backend/app/services/llm.py`)
- Vector DB: Chroma, persisted to `backend/chroma_data/` (`backend/app/vectorstore/`)
- Database: PostgreSQL via SQLAlchemy (`backend/app/db/`)

## Code layout

- `backend/app/api/routes/chat.py` — the single `POST /chat` endpoint
- `backend/app/services/pipeline.py` — orchestrates the request flow above: classify → faq/user_data/rag lookup → confidence check → support escalation
- `backend/app/services/router.py` — query classification (faq / user_data / rag)
- `backend/app/services/faq.py`, `user_data.py`, `rag.py` — the three lookup paths
- `backend/app/services/confidence.py` — confidence scoring gate
- `backend/app/services/support.py` — support ticket creation on low confidence
- `backend/app/db/models.py` — `FAQ` and `SupportTicket` tables

`user_data.lookup_user_data` and the FAQ fuzzy-matching in `faq.lookup_faq` are stubs/TODOs — they need real backend API wiring and FAQ content respectively before the pipeline is fully functional.

## Conventions

- Backend: run from `backend/` with a venv (`python3 -m venv .venv`), deps in `requirements.txt`, config via `.env` (see `.env.example`) loaded through `app/core/config.py` (pydantic-settings).
- Frontend: standard Vite React app in `frontend/`, run with `npm install && npm run dev`.
- Secrets (`GROQ_API_KEY`, `DATABASE_URL`) live in `backend/.env`, which is gitignored — never commit it.
