# TEF Chatbot — Backend

FastAPI service exposing `POST /chat`, backed by a LangGraph pipeline (refine → intent/entities → FAQ layer → knowledge-base layer → confidence gate → synthesis/escalation). See the root [`README.md`](../README.md) for the overall architecture and [`CLAUDE.md`](../CLAUDE.md) for the full reference.

## Setup

```
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

| Key | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq API key, used for every LLM call in the pipeline |
| `GROQ_MODEL` | Groq model id (default `llama-3.3-70b-versatile`) |
| `DATABASE_URL` | Postgres connection string, used only for `support_tickets` |
| `CHROMA_PERSIST_DIR` | Local folder Chroma persists to (default `./chroma_data`) |
| `FAQ_DATA_DIR` / `KB_DATA_DIR` | Source folders for ingestion (default `./faqdata`, `./knowledgebase`) |
| `FAQ_COLLECTION_NAME` / `KB_COLLECTION_NAME` | Chroma collection names |
| `FAQ_TOP_K` / `KB_TOP_K` | How many chunks to retrieve per layer |
| `FAQ_DISTANCE_THRESHOLD` / `KB_DISTANCE_THRESHOLD` | Cosine-distance cutoff for a "match" (lower = stricter) |
| `RETRY_LOOSEN_FACTOR` | How much the threshold relaxes on a layer's 2nd attempt |
| `MAX_LAYER_ATTEMPTS` | Retries per layer before giving up (default 2) |
| `CONFIDENCE_THRESHOLD` | Minimum KB-layer confidence to answer instead of escalating |
| `CONFIDENCE_RETRIEVAL_WEIGHT` | Weight of retrieval-similarity vs. LLM score in the KB confidence hybrid |
| `SUPPORT_EMAIL` / `SUPPORT_PHONE` | Contact info surfaced to the user on escalation |
| `FRONTEND_ORIGIN` | Allowed CORS origin for the React app |

`GROQ_API_KEY` and `DATABASE_URL` are secrets — `.env` is gitignored, never commit it.

## Content layout

FAQs and knowledge-base documents live in parallel, per-category folder trees:

```
backend/
  faqdata/<Category>/*.json        # [{ "question": ..., "answer": ... }, ...]
  knowledgebase/<Category>/*.docx|.pdf|.txt|.md
```

Category names should match across both trees (e.g. `Audit/`, `LMS/`, `Mentorship/`, `M&E/`, `Pitching/`, `Entrepreneur Onboarding/`, `Common/` for general items). `backend/faqdata/` currently only has placeholder/general content — writing real FAQ entries per category is a content task.

## Ingestion

Run after adding/changing content in either folder:

```
python -m scripts.ingest --collection knowledge_base --path ./knowledgebase
python -m scripts.ingest --collection faq             --path ./faqdata
```

Add `--reset` to clear a collection before re-ingesting (e.g. after editing existing docs).

## Running

```
uvicorn app.main:app --reload
```

`GET /health` for a liveness check, `POST /chat` with `{"user_id": "...", "message": "..."}` returning `{answer, confidence, escalated, answered_by, support_email, support_phone, sources}` (`confidence`/`support_*` are `null` unless the KB layer or escalation applies respectively).

## Pipeline internals

- `app/services/graph/state.py` — the shared state schema threaded through every node
- `app/services/graph/pipeline_graph.py` — the LangGraph `StateGraph` wiring (nodes + conditional edges)
- `app/services/query_refiner.py`, `intent_extractor.py` — pre-processing nodes
- `app/services/faq_layer.py`, `kb_layer.py` — the two retrieval layers (each retries up to `MAX_LAYER_ATTEMPTS` times via `app/services/retrieval.py`)
- `app/services/confidence.py` — KB-only confidence gate
- `app/services/synthesis.py` — shared final-answer generation for both success paths
- `app/services/support.py` — support ticket creation + escalation message
