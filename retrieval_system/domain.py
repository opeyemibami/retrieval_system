from dataclasses import dataclass, field


@dataclass
class Document:
    id: str
    title: str
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    id: str
    document_id: str
    text: str
    metadata: dict = field(default_factory=dict)
    parent_chunk_id: str | None = None


@dataclass
class Embedding:
    chunk_id: str
    vector: list[float]


@dataclass
class RetrievedChunk:
    chunk_id: str
    score: float
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ContextBundle:
    query: str
    chunks: list[RetrievedChunk]
