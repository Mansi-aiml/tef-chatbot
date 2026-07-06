"""Seed the FAQ table from a JSON file of {"question": ..., "answer": ...} entries.

Usage:
    python -m scripts.seed_faqs --file scripts/faqs.json
"""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.models import FAQ
from app.db.session import Base, SessionLocal, engine


def load_entries(file_path: Path) -> list[dict]:
    entries = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        sys.exit("expected a JSON array of {question, answer} objects")
    return entries


def seed(entries: list[dict]) -> tuple[int, int]:
    Base.metadata.create_all(engine)

    created = 0
    skipped = 0

    with SessionLocal() as db:
        for entry in entries:
            question = entry["question"].strip()
            answer = entry["answer"].strip()

            existing = db.execute(select(FAQ).where(FAQ.question == question)).scalar_one_or_none()
            if existing is not None:
                skipped += 1
                continue

            db.add(FAQ(question=question, answer=answer))
            created += 1

        db.commit()

    return created, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="JSON file of FAQ entries")
    args = parser.parse_args()

    if not args.file.is_file():
        sys.exit(f"not a file: {args.file}")

    entries = load_entries(args.file)
    created, skipped = seed(entries)
    print(f"done — {created} FAQ(s) created, {skipped} skipped (already existed)")


if __name__ == "__main__":
    main()
