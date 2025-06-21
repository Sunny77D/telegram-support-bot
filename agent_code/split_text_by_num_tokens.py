import pickle
import tiktoken

MAX_TOKEN_PAGE = 30000
MAX_TOKEN_LIMIT = 2000 # The maximum number of tokens for embeddings is 8192, but we use a lower limit to avoid issues with long texts.
OVERLAP_TOKEN_SIZE = 200 # The overlap size to ensure context is preserved when splitting text.

url_to_num_tokens = {}
url_splits_merges_to_text = {}

with open("url_to_all_text.pkl", "rb") as f:
    url_to_text = pickle.load(f)

encoding = tiktoken.get_encoding("cl100k_base")  # for OpenAI models like text-embedding-3-small
for url, text in url_to_text.items():
    if not text.strip():
        continue
    url_to_num_tokens[url] = len(encoding.encode(text))

# In case you want to analyze the number of tokens for each URL's text, you can use the following code snippet.
# print(sorted(url_to_num_tokens.items(), key=lambda x: x[1], reverse=True))

# if the content of a URL is very long, we won't use it
url_to_num_tokens = {url: num_tokens for url, num_tokens in url_to_num_tokens.items() if num_tokens <= MAX_TOKEN_PAGE}

def split_text_by_num_tokens(text, max_tokens=MAX_TOKEN_LIMIT, overlap=OVERLAP_TOKEN_SIZE):
    chunks = []
    tokens = encoding.encode(text)
    i = 0
    while i < len(tokens):
        chunks.append(encoding.decode(tokens[i:max(len(tokens), i + max_tokens)]))
        if i + max_tokens >= len(tokens):
            break
        i += (max_tokens - overlap)
    return chunks

# url_num_tokens_pairs is a list of tuples (url, num_tokens)
def merge_urls(url_to_num_tokens):
    url_num_tokens_pairs = sorted(url_to_num_tokens.items(), key=lambda x: x[1], reverse=True)
    merged_urls, current_urls = [], []
    current_size = 0
    for i in range(len(url_num_tokens_pairs)):
        if current_size + url_num_tokens_pairs[i][1] <= MAX_TOKEN_LIMIT:
            current_urls.append(url_num_tokens_pairs[i][0])
            current_size += url_num_tokens_pairs[i][1]
        else:
            if len(current_urls) > 0:
                merged_urls.append(current_urls)
            current_urls = [url_num_tokens_pairs[i][0]]
            current_size = url_num_tokens_pairs[i][1]
    if len(current_urls) > 0:
        merged_urls.append(current_urls)
    return merged_urls

merged_urls = merge_urls(url_to_num_tokens)
for urls in merged_urls:
    if len(urls) > 1 or url_to_num_tokens[urls[0]] <= MAX_TOKEN_LIMIT:
        url_splits_merges_to_text[" ".join(urls)] = "\n\n".join([url_to_text[url] for url in urls])
    else:
        texts = split_text_by_num_tokens(url_to_text[urls[0]])
        for i, text in enumerate(texts):
            url_splits_merges_to_text[f"{urls[0]}_{i}"] = text

with open("url_splits_merges_to_text.pkl", "wb") as f:
    pickle.dump(url_splits_merges_to_text, f)