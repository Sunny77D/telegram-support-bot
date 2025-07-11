import requests
from bs4 import BeautifulSoup
import time
from supportbot.clients.supabase.supabase_client import Supabase
from chunk_utils import get_identifier_to_num_tokens, merge_split_identifiers
import asyncio

BASE_URL = "https://app.artemis.xyz/docs/overview"
URL_PREFIX = "https://app.artemis.xyz"
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

if __name__ == "__main__":

    url_to_text = crawl(BASE_URL, True)
    print(f"\n✅ Crawled {len(url_to_text)} pages.")

    url_to_num_tokens = get_identifier_to_num_tokens(url_to_text)
    crawled_chunks = merge_split_identifiers(url_to_text, url_to_num_tokens)
    supabase_client = Supabase()

    async def insert_chunks():
        for crawled_chunk in crawled_chunks:
            crawled_chunk_data = {
                'url': crawled_chunk.identifier,
                'chunk_number': crawled_chunk.chunk_id,
                'chunk': crawled_chunk.text
            }
            result = await supabase_client.insert_row(table='crawled_url_chunks', dict=crawled_chunk_data)
            if result is None:
                print(f"Failed to insert chunk to DB: {crawled_chunk.url} - {crawled_chunk.chunk_id}")

    asyncio.run(insert_chunks())
        