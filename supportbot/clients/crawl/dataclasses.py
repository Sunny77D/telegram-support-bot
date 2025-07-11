from dataclasses import dataclass

@dataclass
class CrawlChunk:
    url: str
    chunk_id: int
    text: str

@dataclass
class ChunkAndEmbedding:
    chunk: str
    embedding: list[float]
