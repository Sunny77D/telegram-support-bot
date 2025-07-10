from dataclasses import dataclass

@dataclass
class CrawlChunk:
    url: str
    chunk_id: int
    text: str
