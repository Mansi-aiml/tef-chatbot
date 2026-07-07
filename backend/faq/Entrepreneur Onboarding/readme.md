# Entrepreneur Onboarding FAQs

Add one or more `*.json` files here (any filename) with this shape:

```json
[
  { "question": "What documents do I need to complete onboarding?", "answer": "..." },
  { "question": "How long does entrepreneur onboarding take?", "answer": "..." }
]
```

After adding/editing files, re-ingest from `backend/`:

```
python -m scripts.ingest --collection faq --path ./faq --reset
```

(`--reset` clears the FAQ collection first — needed if you edited or removed existing entries, not just added new ones.)
