import os , requests

URL = "https://books.toscrape.com/"
CACHE_FILE = "cache/catalogue-page-1.html"

headers = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/safiya-t/FlyRank-Internship.git)"
}
os.makedirs("cache", exist_ok=True)

if os.path.exists(CACHE_FILE):

    print("CACHE HIT")

    with open(CACHE_FILE, "r", encoding="utf-8") as file:
        html = file.read()

else:

    print("FETCH")

    response = requests.get(
        URL,
        headers=headers,
        timeout=10
    )
    if response.status_code != 200:
        raise Exception(
            f"Fetch failed with status {response.status_code}"
        )

    html = response.text

    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        file.write(html)

print(f"Response size: {len(html)} bytes")