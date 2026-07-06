from app.vectorstore.chroma_client import query_knowledge_base

results = query_knowledge_base(
    "How do I create a mentor?"
)

for i, result in enumerate(results, 1):
    print(f"\nResult {i}")
    print("-" * 50)
    print("Distance:", result["distance"])
    print("Source:", result["metadata"]["source"])
    print(result["document"][:500])