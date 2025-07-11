from dataclasses import dataclass

@dataclass
class GenericChunk:
    identifier: str
    chunk_id: int
    text: str

@dataclass
class ChunkAndEmbedding:
    chunk: str
    embedding: list[float]
