import os , requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://books.toscrape.com/"
CACHE_FILE = "cache/catalogue-page-1.html"

headers = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/safiya-t/FlyRank-Internship.git)"
}

os.makedirs("cache", exist_ok=True)

books = []

for page in range(1, 4):

    cache = f"cache/catalogue-page-{page}.html"

    if os.path.exists(cache):
        print(f"CACHE HIT: page {page}")
        html = open(cache, encoding="utf-8").read()

    else:
        print(f"FETCH: page {page}")

        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            raise Exception(f"Fetch failed: {r.status_code}")

        html = r.text
        open(cache, "w", encoding="utf-8").write(html)

        time.sleep(0.5)

    soup = BeautifulSoup(html, "html.parser")

    for book in soup.select("article.product_pod h3 a"):
        books.append(urljoin(url, book["href"]))

    next_link = soup.select_one("li.next a")

    if next_link:
        url = urljoin(url, next_link["href"])

books = list(dict.fromkeys(books))

print(f"catalogue_pages=3")
print(f"discovered={len(books)}")
print(f"unique_urls={len(books)}")