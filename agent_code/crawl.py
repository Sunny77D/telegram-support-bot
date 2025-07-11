import requests
from bs4 import BeautifulSoup
import time
import tiktoken
from supportbot.clients.crawl.dataclasses import CrawlChunk
from supportbot.clients.supabase.supabase_client import Supabase
import asyncio

BASE_URL = "https://app.artemis.xyz/docs/overview"
URL_PREFIX = "https://app.artemis.xyz"
MAX_TOKEN_PAGE = 30000
MAX_TOKEN_LIMIT = 2000 # The maximum number of tokens for embeddings is 8192, but we use a lower limit to avoid issues with long texts.
OVERLAP_TOKEN_SIZE = 200 # The overlap size to ensure context is preserved when splitting text.
MAX_CRAWL_PAGES = 5000  # Limit the number of pages to crawl

def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove navbars, sidebars, etc. if needed (tweak as needed)
    # TODO: might need to re-evaluate how to better clean the text since the reulting text is not very readable
    for tag in soup(["script", "style", "nav", "footer", "header", "svg", "link", "meta", 'circle']):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text

# Crawl pages recursively; don't recurrently follow links that are not part of the docs (depth 1)
def crawl(url : str, recurrent: bool) -> dict[str, str]:
    docs = {}
    failed_urls = set()
    def crawl_recurrent(url, recurrent):
        if len(docs) >= MAX_CRAWL_PAGES or url in docs or url in failed_urls:
            return

        try:
            print(f"Crawling: {url}")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()

            # TODO: this code doesn't work for JavaScript-rendered web pages such as https://app.hex.tech/c46e17df-7be4-4ce4-ad87-cfae2edb1e6b/app/01976433-99a0-7002-9850-14fcfb0979ee/latest
            # We probably have to use a headless browser like Selenium or Playwright for those cases but I think we might need log in as well
            # The following code still doesn't work for the above page:
            # from selenium import webdriver
            # driver = webdriver.Chrome()
            # driver.get(url)
            # driver.page_source is supposed to have the rendered HTML but it's still missing the content
            text = clean_text(resp.text)
            docs[url] = text

            soup = BeautifulSoup(resp.text, "html.parser")
            for link_tag in soup.find_all("a", href=True):
                href = link_tag['href']
                # TODO: this is a solution particular for the artemis docs, we need better logic to handle relative links
                if recurrent:
                    time.sleep(0.3)
                    if href.startswith('/docs/'): 
                        crawl_recurrent(URL_PREFIX + href, True)
                    else:
                        crawl_recurrent(href, False)

        except Exception as e:
            failed_urls.add(url)
            print(f"Failed to crawl {url}: {e}")
    crawl_recurrent(url, recurrent)
    return docs

def get_url_to_num_tokens(url_to_text: dict[str, str]) -> dict[str, int]:
    url_to_num_tokens = {}
    encoding = tiktoken.get_encoding("cl100k_base")  # for OpenAI models like text-embedding-3-small

    for url, text in url_to_text.items():
        if not text.strip():
            continue
        # if the content of a URL is very long, we won't use it
        if len(encoding.encode(text)) <= MAX_TOKEN_PAGE:
            url_to_num_tokens[url] = len(encoding.encode(text))
    return url_to_num_tokens

# In case you want to analyze the number of tokens for each URL's text, you can use the following code snippet.
# print(sorted(url_to_num_tokens.items(), key=lambda x: x[1], reverse=True))

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

# url_num_tokens_pairs is a list of tuples (url, num_tokens)
def merge_urls(url_to_num_tokens) -> list[list[str]]:
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

def merge_split_urls(url_to_text : dict[str, str], url_to_num_tokens : dict[str, int]) -> list[CrawlChunk]:
    crawl_chunks = []
    merged_urls = merge_urls(url_to_num_tokens)
    for urls in merged_urls:
        if len(urls) > 1 or url_to_num_tokens[urls[0]] <= MAX_TOKEN_LIMIT:
            crawl_chunks.append(
                CrawlChunk(
                    url=" ".join(urls),
                    chunk_id=0,
                    text="\n\n".join([url_to_text[url] for url in urls])
                )
            )
        else:
            texts = split_text_by_num_tokens(url_to_text[urls[0]])
            for i, text in enumerate(texts):
                crawl_chunks.append(
                    CrawlChunk(
                        url=urls[0],
                        chunk_id=i,
                        text=text
                    )
                )
    return crawl_chunks

if __name__ == "__main__":

    url_to_text = crawl(BASE_URL, True)
    print(f"\n✅ Crawled {len(url_to_text)} pages.")

    url_to_num_tokens = get_url_to_num_tokens(url_to_text)
    crawled_chunks = merge_split_urls(url_to_text, url_to_num_tokens)
    supabase_client = Supabase()

    async def insert_chunks():
        for crawled_chunk in crawled_chunks:
            crawled_chunk_data = {
                'url': crawled_chunk.url,
                'chunk_number': crawled_chunk.chunk_id,
                'chunk': crawled_chunk.text
            }
            result = await supabase_client.insert_row(table='crawled_url_chunks', dict=crawled_chunk_data)
            if result is None:
                print(f"Failed to insert chunk to DB: {crawled_chunk.url} - {crawled_chunk.chunk_id}")

    asyncio.run(insert_chunks())
        