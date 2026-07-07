# Audit FAQs

Add one or more `*.json` files here (any filename) with this shape:

```json
[
  { "question": "How do I start a new audit review?", "answer": "..." },
  { "question": "Who can approve an audit finding?", "answer": "..." }
]
```

After adding/editing files, re-ingest from `backend/`:

```
python -m scripts.ingest --collection faq --path ./faq --reset
```

(`--reset` clears the FAQ collection first — needed if you edited or removed existing entries, not just added new ones.)
