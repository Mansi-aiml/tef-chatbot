# TEF Chatbot

A chatbot that answers user queries using FAQs, user data, and a knowledge base (RAG). Low-confidence answers get escalated to support instead of being sent to the user.

## How it works

1. User sends a message from the frontend.
2. The query is refined, classified, and routed.
3. Depending on the query type, it looks up:
   - FAQ (direct match)
   - User data (via backend API)
   - Knowledge base (vector search / RAG)
4. If no direct FAQ answer is found, it falls back to RAG search.
5. A response is generated from the retrieved info.
6. Confidence check:
   - High confidence → answer sent to user
   - Low confidence → support ticket created + user notified

## Features

- Query understanding & routing
- FAQ lookup
- User data lookup
- Knowledge base RAG search
- Response generation
- Confidence-based escalation to support

## Tech Stack

- Frontend: React (Vite)
- Backend: Python (FastAPI)
- LLM: Groq
- Vector DB: Chroma
- Database: PostgreSQL

## Project structure

```
frontend/   React + Vite SPA
backend/    FastAPI app
  app/main.py            entrypoint, CORS, router registration
  app/api/routes/         HTTP endpoints (POST /chat)
  app/services/           pipeline: router -> faq/user_data/rag -> confidence -> support
  app/db/                 SQLAlchemy models + session (PostgreSQL)
  app/vectorstore/        Chroma client
  app/core/config.py       env-based settings
```

## Getting started

### Backend

```
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY and DATABASE_URL
uvicorn app.main:app --reload
```

### Frontend

```
cd frontend
npm install
npm run dev
```

Requires a running PostgreSQL instance matching `DATABASE_URL` and a `GROQ_API_KEY` for the LLM calls. Chroma persists locally to `backend/chroma_data/` (no separate service needed).

