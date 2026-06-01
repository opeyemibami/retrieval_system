from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from retrieval_system.domain import Document
from retrieval_system.storage.database import get_connection


class DocumentStore:
    def __init__(self, connection: Any | None = None):
        self.connection = connection or get_connection()

    def save_document(self, document: Document) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (id, title, content, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    document.id,
                    document.title,
                    document.content,
                    Jsonb(document.metadata),
                ),
            )
        self.connection.commit()

    def get_document(self, document_id: str) -> Document | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, content, metadata
                FROM documents
                WHERE id = %s;
                """,
                (document_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_document(row)

    def list_documents(self) -> list[Document]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, content, metadata
                FROM documents
                ORDER BY created_at ASC;
                """
            )
            rows = cursor.fetchall()

        return [self._row_to_document(row) for row in rows]

    def document_exists(self, document_id: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM documents
                WHERE id = %s
                LIMIT 1;
                """,
                (document_id,),
            )
            return cursor.fetchone() is not None

    def _row_to_document(self, row: Any) -> Document:
        if isinstance(row, dict):
            return Document(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                metadata=row["metadata"] or {},
            )

        return Document(
            id=row[0],
            title=row[1],
            content=row[2],
            metadata=row[3] or {},
        )
