"""Load .txt/.md/.pdf files from a folder into the Chroma knowledge base.

Usage:
    python -m scripts.ingest_documents --path ./docs
    python -m scripts.ingest_documents --path ./docs --reset
"""

import argparse
import sys
import uuid
from pathlib import Path

from app.vectorstore.chroma_client import knowledge_base

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


def load_text(file_path: Path) -> str:
    if file_path.suffix == ".pdf":
        from pypdf import PdfReader

    elif file_path.suffix == ".docx":
        from docx import Document

        doc = Document(str(file_path))
        return "\n\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
    return file_path.read_text(encoding="utf-8")


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > chunk_size:
            chunks.append(current)
            current = current[-chunk_overlap:] if chunk_overlap else ""
        current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)

    return chunks


def iter_documents(root: Path):
    for file_path in sorted(root.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield file_path


def ingest(root: Path, chunk_size: int, chunk_overlap: int) -> int:
    total_chunks = 0

    for file_path in iter_documents(root):
        text = load_text(file_path)
        if not text.strip():
            print(f"skip (empty): {file_path}")
            continue

        chunks = chunk_text(text, chunk_size, chunk_overlap)
        source = str(file_path.relative_to(root))

        knowledge_base.add(
            ids=[f"{source}::{i}::{uuid.uuid4().hex[:8]}" for i in range(len(chunks))],
            documents=chunks,
            metadatas=[{"source": source, "chunk": i} for i in range(len(chunks))],
        )

        print(f"ingested {len(chunks)} chunk(s) from {source}")
        total_chunks += len(chunks)

    return total_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, type=Path, help="Folder containing .txt/.md/.pdf files")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Max characters per chunk")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Characters of overlap between chunks")
    parser.add_argument("--reset", action="store_true", help="Delete all existing entries before ingesting")
    args = parser.parse_args()

    if not args.path.is_dir():
        sys.exit(f"not a directory: {args.path}")

    if args.reset:
        existing = knowledge_base.get()["ids"]
        if existing:
            knowledge_base.delete(ids=existing)
        print(f"cleared {len(existing)} existing entr(ies)")

    total = ingest(args.path, args.chunk_size, args.chunk_overlap)
    print(f"done — {total} chunk(s) ingested")


if __name__ == "__main__":
    main()
