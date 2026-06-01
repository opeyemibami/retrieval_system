from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


DEFAULT_DATABASE_URL = "postgresql://retrieval:retrieval@localhost:5432/retrieval"


def get_connection() -> psycopg.Connection:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return psycopg.connect(database_url, row_factory=dict_row)


def init_db() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    metadata    JSONB DEFAULT '{}',
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id               TEXT PRIMARY KEY,
                    document_id      TEXT NOT NULL REFERENCES documents(id),
                    parent_chunk_id  TEXT REFERENCES chunks(id),
                    text             TEXT NOT NULL,
                    metadata         JSONB DEFAULT '{}',
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS retrieval_runs (
                    id              TEXT PRIMARY KEY,
                    config          JSONB NOT NULL,
                    created_at      TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    id               TEXT PRIMARY KEY,
                    retrieval_run_id TEXT REFERENCES retrieval_runs(id),
                    query            TEXT NOT NULL,
                    metrics          JSONB NOT NULL,
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
        connection.commit()
