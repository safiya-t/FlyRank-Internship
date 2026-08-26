import os , requests
import time ,json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime , timezone
from pydantic import BaseModel , HttpUrl

url = "https://books.toscrape.com/"
CACHE_FILE = "cache/catalogue-page-1.html"

headers = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/safiya-t/FlyRank-Internship.git)"
}

os.makedirs("cache", exist_ok=True)
os.makedirs("output", exist_ok=True)

class Book(BaseModel):
    title: str
    product_url:str
    price_text: str
    price_gbp:float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: str

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

valid_records = []
errors = []

for record in records:
    try:
        price_text = record["price_text"]

        price_gbp = float(
            price_text.replace("Â£", "").replace("£", "").strip()
        )
        record["price_gbp"] = price_gbp
        if not record["product_url"].startswith("https://"):
            raise ValueError("product_url must start with https://")

        if not record["source_page"].startswith("https://"):
           raise ValueError("source_page must start with https://")
        book = Book(**record)
        valid_records.append(book.model_dump(mode="json"))


    except Exception as e:

        errors.append({
            "record": record,
            "reason": str(e)
        })

unique_records = {}
 
for record in valid_records:

    unique_records[str(record["product_url"])] = record

valid_records = list(unique_records.values())

with open("output/books.json", "w", encoding="utf-8") as f:

    json.dump(
        valid_records,
        f,
        indent=2,
        ensure_ascii=False
    )

with open("output/errors.json", "w", encoding="utf-8") as f:

    json.dump(
        errors,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\nSTAGE 4 SUMMARY")

print(f"valid_records={len(valid_records)}")
print(f"invalid_records={len(errors)}")

print("Saved: output/books.json")
print("Saved: output/errors.json")