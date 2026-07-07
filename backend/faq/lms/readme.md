# LMS FAQs

Add one or more `*.json` files here (any filename) with this shape:

```json
[
  { "question": "How do I enroll in a course on the LMS?", "answer": "..." },
  { "question": "Where can I find my course completion certificate?", "answer": "..." }
]
```

After adding/editing files, re-ingest from `backend/`:

```
python -m scripts.ingest --collection faq --path ./faq --reset
```

(`--reset` clears the FAQ collection first — needed if you edited or removed existing entries, not just added new ones.)
