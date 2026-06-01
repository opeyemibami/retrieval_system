from __future__ import annotations

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieval_system.ingestion.arxiv_source import ArxivSource
from retrieval_system.storage.database import init_db
from retrieval_system.storage.document_store import DocumentStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest arXiv papers into PostgreSQL.")
    parser.add_argument("--query", required=True, help="arXiv search query string")
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Number of papers to fetch",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    init_db()

    source = ArxivSource(query=args.query, max_results=args.max_results)
    store = DocumentStore()

    documents = source.fetch_documents()
    new_count = 0

    for document in documents:
        if store.document_exists(document.id):
            continue

        store.save_document(document)
        new_count += 1

    print(f"Fetched {len(documents)} documents; saved {new_count} new documents.")


if __name__ == "__main__":
    main()
