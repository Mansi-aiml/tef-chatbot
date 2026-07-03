import chromadb

from app.core.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

knowledge_base = _client.get_or_create_collection(name="knowledge_base")


def query_knowledge_base(query: str, n_results: int = 3) -> list[dict]:
    results = knowledge_base.query(query_texts=[query], n_results=n_results)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    return [
        {"document": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]
