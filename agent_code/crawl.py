import requests
from bs4 import BeautifulSoup
import pickle
import time

BASE_URL = "https://app.artemis.xyz/docs/overview"
URL_PREFIX = "https://app.artemis.xyz"
docs = {}
failed_urls = set()

def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove navbars, sidebars, etc. if needed (tweak as needed)
    # TODO: might need to re-evaluate how to better clean the text since the reulting text is not very readable
    for tag in soup(["script", "style", "nav", "footer", "header", "svg", "link", "meta", 'circle']):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text

# Crawl pages recursively; don't recurrently follow links that are not part of the docs (depth 1)
def crawl(url, recurrent):
    if len(docs) >= 5000 or url in docs or url in failed_urls:
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
                    crawl(URL_PREFIX + href, True)
                else:
                    crawl(href, False)

    except Exception as e:
        failed_urls.add(url)
        print(f"Failed to crawl {url}: {e}")

crawl(BASE_URL, True)

with open("url_to_all_text.pkl", "wb") as f:
    pickle.dump(docs, f)

print(f"\n✅ Crawled {len(docs)} pages.")
