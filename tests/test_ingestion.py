from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from retrieval_system.domain import Document
from retrieval_system.ingestion.arxiv_source import ArxivSource
from retrieval_system.storage.document_store import DocumentStore


class FakeCursor:
    def __init__(self, connection: FakeConnection):
        self.connection = connection
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query, params=None):
        normalized_query = " ".join(query.split()).upper()

        if normalized_query.startswith("INSERT INTO DOCUMENTS"):
            document_id, title, content, metadata = params
            self.connection.documents[document_id] = {
                "id": document_id,
                "title": title,
                "content": content,
                "metadata": metadata.obj,
            }
            self.result = None
            return

        if "SELECT 1 FROM DOCUMENTS" in normalized_query:
            document_id = params[0]
            self.result = (1,) if document_id in self.connection.documents else None
            return

        if "SELECT ID, TITLE, CONTENT, METADATA FROM DOCUMENTS WHERE ID" in normalized_query:
            document_id = params[0]
            self.result = self.connection.documents.get(document_id)
            return

        if "SELECT ID, TITLE, CONTENT, METADATA FROM DOCUMENTS ORDER BY" in normalized_query:
            self.result = list(self.connection.documents.values())
            return

        raise AssertionError(f"Unexpected query: {query}")

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result


class FakeConnection:
    def __init__(self):
        self.documents = {}
        self.commits = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1


class FakeArxivClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def results(self, search):
        return [
            SimpleNamespace(
                entry_id="https://arxiv.org/abs/2401.00001v1",
                title=" Test Paper ",
                summary=" Test abstract. ",
                authors=[SimpleNamespace(name="Ada Lovelace")],
                categories=["cs.IR"],
                published=datetime(2024, 1, 1, tzinfo=timezone.utc),
                get_short_id=lambda: "2401.00001v1",
            )
        ]


def test_arxiv_source_fetch_documents_returns_documents():
    with patch("retrieval_system.ingestion.arxiv_source.arxiv.Client", FakeArxivClient):
        documents = ArxivSource(query="cat:cs.IR", max_results=1).fetch_documents()

    assert isinstance(documents, list)
    assert all(isinstance(document, Document) for document in documents)


def test_arxiv_source_documents_have_required_fields():
    with patch("retrieval_system.ingestion.arxiv_source.arxiv.Client", FakeArxivClient):
        documents = ArxivSource(query="cat:cs.IR", max_results=1).fetch_documents()

    document = documents[0]
    assert document.id
    assert document.title
    assert document.content
    assert document.metadata["authors"] == ["Ada Lovelace"]
    assert document.metadata["categories"] == ["cs.IR"]
    assert document.metadata["published"] == "2024-01-01"


def test_document_store_save_document_persists_document():
    store = DocumentStore(connection=FakeConnection())
    document = Document(
        id="doc-1",
        title="A Document",
        content="Document content",
        metadata={"source": "test"},
    )

    store.save_document(document)

    assert store.get_document("doc-1") == document


def test_document_store_document_exists_returns_true_after_save():
    store = DocumentStore(connection=FakeConnection())

    store.save_document(Document(id="doc-1", title="A Document", content="Content"))

    assert store.document_exists("doc-1") is True


def test_document_store_document_exists_returns_false_for_unknown_id():
    store = DocumentStore(connection=FakeConnection())

    assert store.document_exists("unknown") is False
