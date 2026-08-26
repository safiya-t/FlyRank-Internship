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

start_time = datetime.now(timezone.utc)

pages_fetched = 0
cache_hits = 0
failed_pages = []    

books = []
page_url = url

for page in range(1, 4):

    cache = f"cache/catalogue-page-{page}.html"

    if os.path.exists(cache):

        print(f"CACHE HIT: page {page}")

        with open(cache, encoding="utf-8") as f:
            html = f.read()

        cache_hits += 1

    else:

        print(f"FETCH: page {page}")

        r = requests.get(
            page_url,
            headers=headers,
            timeout=10
        )

        if r.status_code != 200:
            raise Exception(
                f"Fetch failed: {r.status_code}"
            )

        html = r.text

        with open(
            cache,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(html)

        pages_fetched += 1

        time.sleep(0.5)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for book in soup.select(
        "article.product_pod h3 a"
    ):

        books.append({
            "url": urljoin(
                page_url,
                book["href"]
            ),
            "source_page": page_url
        })

    next_link = soup.select_one(
        "li.next a"
    )

    if next_link:

        page_url = urljoin(
            page_url,
            next_link["href"]
        )

unique_books = []
seen = set()

for book in books:

    if book["url"] not in seen:

        seen.add(book["url"])
        unique_books.append(book)

books = unique_books


print("catalogue_pages=3")
print(f"discovered={len(books)}")
print(f"unique_urls={len(books)}")
#test
books.append({
    "url": "https://books.toscrape.com/fake-book-that-does-not-exist",
    "source_page": page_url
})

print(f"TEST URL ADDED: {books[-1]['url']}")


records = []

for i, book in enumerate(books, 1):

    book_url = book["url"]
    source_page = book["source_page"]

    cache_file = f"cache/book-{i}.html"

    try:
        if os.path.exists(cache_file):

            print(f"CACHE HIT: book {i}")

            with open(
                cache_file,
                encoding="utf-8"
            ) as f:
                html = f.read()

            cache_hits += 1

        else:

            print(f"FETCH: book {i}")
            for attempt in range(2):

                try:

                    r = requests.get(
                        book_url,
                        headers=headers,
                        timeout=10
                    )

                except requests.exceptions.Timeout:

                    if attempt == 0:

                        print(
                            f"TIMEOUT: book {i} - retrying once"
                        )

                        time.sleep(1)

                        continue

                    raise Exception(
                        "Timeout after retry"
                    )

                if r.status_code == 200:

                    html = r.text

                    with open(
                        cache_file,
                        "w",
                        encoding="utf-8"
                    ) as f:
                        f.write(html)

                    pages_fetched += 1

                    time.sleep(0.5)

                    break

                if 500 <= r.status_code <= 599:

                    if attempt == 0:

                        print(
                            f"SERVER ERROR {r.status_code}: "
                            f"book {i} - retrying once"
)

                        time.sleep(1)

                        continue

                    raise Exception(
                        f"HTTP {r.status_code} after retry"
                    )

                raise Exception(
                    f"HTTP {r.status_code}"
                )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        title = soup.select_one(
            "div.product_main h1"
        )

        price = soup.select_one(
            "div.product_main p.price_color"
        )

        availability = soup.select_one(
            "div.product_main p.instock"
        )

        rating = soup.select_one(
            "div.product_main p.star-rating"
        )

        description = soup.select_one(
            "#product_description + p"
        )

        record = {

            "title": (
                title.get_text(strip=True)
                if title else None
            ),

            "product_url": book_url,

            "price_text": (
                price.get_text(strip=True)
                if price else None
            ),

            "availability_text": (
                availability.get_text(
                    " ",
                    strip=True
                )
                if availability else None
            ),

            "rating_text": (
                " ".join(
                    rating.get("class", [])[1:]
                )
                if rating else None
            ),

            "description": (
                description.get_text(
                    " ",
                    strip=True
                )
                if description else None
            ),

            "source_page": source_page,

            "fetched_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        records.append(record)

    except Exception as e:

        print(
            f"FAILED: book {i} - {book_url}"
        )

        print(
            f"REASON: {e}"
        )

        failed_pages.append({
            "url": book_url,
            "error": str(e)
        })

        continue

print(f"detail_pages={len(records)}")

if records:

    print("\nONE RAW RECORD:")
    print(records[0])

valid_records = []
errors = []

for record in records:

    try:

        price_text = record["price_text"]

        price_gbp = float(
            price_text
            .replace("Â£", "")
            .replace("£", "")
            .strip()
        )

        record["price_gbp"] = price_gbp

        if not record["product_url"].startswith(
            "https://"
        ):

            raise ValueError(
                "product_url must start with https://"
            )

        if not record["source_page"].startswith(
            "https://"
        ):

            raise ValueError(
                "source_page must start with https://"
            )

        book = Book(**record)

        valid_records.append(
            book.model_dump(mode="json")
        )

    except Exception as e:

        errors.append({
            "record": record,
            "reason": str(e)
        })

unique_records = {}

for record in valid_records:

    unique_records[
        str(record["product_url"])
    ] = record

valid_records = list(
    unique_records.values()
)

with open(
    "output/books.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        valid_records,
        f,
        indent=2,
        ensure_ascii=False
    )

with open(
    "output/errors.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        errors,
        f,
        indent=2,
        ensure_ascii=False
    )

end_time = datetime.now(timezone.utc)

duration = (
    end_time - start_time
).total_seconds()

run_report = {

    "start_time": start_time.isoformat(),

    "duration_seconds": round(
        duration,
        2
    ),

    "pages_fetched": pages_fetched,

    "cache_hits": cache_hits,

    "valid_records": len(valid_records),

    "invalid_records": len(errors),

    "failed_pages": len(failed_pages)
}

with open(
    "output/run-report.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        run_report,
        f,
        indent=2
    )

print("\nSTAGE 5 SUMMARY")

print(
    f"pages_fetched={pages_fetched}"
)

print(
    f"cache_hits={cache_hits}"
)

print(
    f"detail_pages={len(records)}"
)

print(
    f"valid_records={len(valid_records)}"
)

print(
    f"invalid_records={len(errors)}"
)

print(
    f"failed_pages={len(failed_pages)}"
)

print(
    "Saved: output/books.json"
)

print(
    "Saved: output/errors.json"
)

print(
    "Saved: output/run-report.json"
)
