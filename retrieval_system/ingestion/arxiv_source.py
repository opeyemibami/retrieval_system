from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import arxiv

from retrieval_system.domain import Document


class DocumentSource(ABC):
    @abstractmethod
    def fetch_documents(self) -> list[Document]:
        ...


class ArxivSource(DocumentSource):
    def __init__(self, query: str, max_results: int = 50):
        self.query = query
        self.max_results = max_results

    def fetch_documents(self) -> list[Document]:
        search = arxiv.Search(
            query=self.query,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        client = arxiv.Client(page_size=max(1, min(self.max_results, 100)))

        return [self._to_document(result) for result in client.results(search)]

    def _to_document(self, result: Any) -> Document:
        return Document(
            id=self._paper_id(result),
            title=result.title.strip(),
            content=result.summary.strip(),
            metadata={
                "authors": [author.name for author in result.authors],
                "categories": list(result.categories),
                "published": self._published_date(result.published),
            },
        )

    def _paper_id(self, result: Any) -> str:
        if hasattr(result, "get_short_id"):
            return result.get_short_id()

        return result.entry_id.rsplit("/", maxsplit=1)[-1]

    def _published_date(self, published: datetime) -> str:
        return published.date().isoformat()
