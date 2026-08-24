import os , requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime , timezone

url = "https://books.toscrape.com/"
CACHE_FILE = "cache/catalogue-page-1.html"

headers = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/safiya-t/FlyRank-Internship.git)"
}

os.makedirs("cache", exist_ok=True)

books = []
page_url = url

for page in range(1, 4):

    cache = f"cache/catalogue-page-{page}.html"

    if os.path.exists(cache):
        print(f"CACHE HIT: page {page}")
        html = open(cache, encoding="utf-8").read()

    else:
        print(f"FETCH: page {page}")

        r = requests.get(page_url, headers=headers, timeout=10)

        if r.status_code != 200:
            raise Exception(f"Fetch failed: {r.status_code}")

        html = r.text
        open(cache, "w", encoding="utf-8").write(html)

        time.sleep(0.5)

    soup = BeautifulSoup(html, "html.parser")

    for book in soup.select("article.product_pod h3 a"):
        books.append({
            "url": urljoin(page_url, book["href"]),
            "source_page": page_url
        })

    next_link = soup.select_one("li.next a")

    if next_link:
        url = urljoin(url, next_link["href"])

unique_books = []
seen = set()

for book in books:
    if book["url"] not in seen:
        seen.add(book["url"])
        unique_books.append(book)

books = unique_books

print(f"catalogue_pages=3")
print(f"discovered={len(books)}")
print(f"unique_urls={len(books)}")

records = []

for i, book in enumerate(books, 1):

    book_url = book["url"]
    source_page = book["source_page"]

    cache_file = f"cache/book-{i}.html"

    if os.path.exists(cache_file):
        print(f"CACHE HIT: book {i}")
        html = open(cache_file, encoding="utf-8").read()

    else:
        print(f"FETCH: book {i}")

        r = requests.get(
            book_url,
            headers=headers,
            timeout=10
        )

        if r.status_code != 200:
            print(f"FAILED: {book_url}")
            continue

        html = r.text

        open(cache_file, "w", encoding="utf-8").write(html)

        time.sleep(0.5)

    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("div.product_main h1")
    price = soup.select_one("div.product_main p.price_color")
    availability = soup.select_one("div.product_main p.instock")
    rating = soup.select_one("div.product_main p.star-rating")
    description = soup.select_one("#product_description + p")

    record = {
        "title": title.get_text(strip=True) if title else None,
        "product_url": book_url,
        "price_text": price.get_text(strip=True) if price else None,
        "availability_text": (
            availability.get_text(" ", strip=True)
            if availability else None
        ),
        "rating_text": (
            " ".join(rating.get("class", [])[1:])
            if rating else None
        ),
        "description": (
            description.get_text(" ", strip=True)
            if description else None
        ),
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

    records.append(record)

print(f"detail_pages={len(records)}")

print("\nONE RAW RECORD:")
print(records[0])