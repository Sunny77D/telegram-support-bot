import tiktoken
from supportbot.clients.crawl.dataclasses import GenericChunk

MAX_TOKEN = 30000
OVERLAP_TOKEN_SIZE = 200 # The overlap size to ensure context is preserved when splitting text.
MAX_TOKEN_LIMIT = 2000 # The maximum number of tokens for embeddings is 8192, but we use a lower limit to avoid issues with long texts.

def get_identifier_to_num_tokens(identifier_to_text: dict[str, str]) -> dict[str, int]:
    identifier_to_num_tokens = {}
    encoding = tiktoken.get_encoding("cl100k_base")  # for OpenAI models like text-embedding-3-small

    for identifier, text in identifier_to_text.items():
        if not text.strip():
            continue
        # if the content of a URL is very long, we won't use it
        if len(encoding.encode(text)) <= MAX_TOKEN:
            identifier_to_num_tokens[identifier] = len(encoding.encode(text))
    return identifier_to_num_tokens

def split_text_by_num_tokens(text : str, max_tokens=MAX_TOKEN_LIMIT, overlap=OVERLAP_TOKEN_SIZE) -> list[str]:
    chunks = []
    encoding = tiktoken.get_encoding("cl100k_base")  # for OpenAI models like text-embedding-3-small
    tokens = encoding.encode(text)
    i = 0
    while i < len(tokens):
        chunks.append(encoding.decode(tokens[i:max(len(tokens), i + max_tokens)]))
        if i + max_tokens >= len(tokens):
            break
        i += (max_tokens - overlap)
    return chunks

def merge_identifiers(identifier_to_num_tokens : dict[str, int]) -> list[list[str]]:
    identifier_num_tokens_pairs = sorted(identifier_to_num_tokens.items(), key=lambda x: x[1], reverse=True)
    merged_identifiers, current_identifiers = [], []
    current_size = 0
    for i in range(len(identifier_num_tokens_pairs)):
        if current_size + identifier_num_tokens_pairs[i][1] <= MAX_TOKEN_LIMIT:
            current_urls.append(identifier_num_tokens_pairs[i][0])
            current_size += identifier_num_tokens_pairs[i][1]
        else:
            if len(current_identifiers) > 0:
                merged_identifiers.append(current_urls)
            current_urls = [identifier_num_tokens_pairs[i][0]]
            current_size = identifier_num_tokens_pairs[i][1]
    if len(current_urls) > 0:
        merged_identifiers.append(current_urls)
    return merged_identifiers

def merge_split_identifiers(identifier_to_text : dict[str, str], identifier_to_num_tokens : dict[str, int]) -> list[GenericChunk]:
    crawl_chunks = []
    merged_identifiers = merge_identifiers(identifier_to_num_tokens)
    for identifiers in merged_identifiers:
        if len(identifiers) > 1 or identifier_to_num_tokens[identifiers[0]] <= MAX_TOKEN_LIMIT:
            crawl_chunks.append(
                GenericChunk(
                    identifier=" ".join(identifiers),
                    chunk_id=0,
                    text="\n\n".join([identifier_to_text[identifier] for identifier in identifiers])
                )
            )
        else:
            texts = split_text_by_num_tokens(identifier_to_text[identifiers[0]])
            for i, text in enumerate(texts):
                crawl_chunks.append(
                    GenericChunk(
                        identifier=identifiers[0],
                        chunk_id=i,
                        text=text
                    )
                )
    return crawl_chunks
