# Polite Scraper

A small Python web scraping project for the FlyRank Internship Week 5 assignment.

## Description

This project implements a small, polite web scraping pipeline for **Books to Scrape**, a public practice sandbox created for learning web scraping.

The scraper downloads the first three catalogue pages, discovers the book links, visits all 60 book pages, extracts book information, cleans and validates the data, and stores the results as JSON.

The scraper also uses caching to avoid unnecessary repeated requests, handles failed pages without stopping the entire run, and generates a run report containing useful statistics about each execution.

## Site: Books to Scrape

It is a public practice sandbox specifically created for beginners to practice web scraping.

## Why Books to Scrape?

This site is suitable for this assignment because it is publicly available as a practice sandbox for web scraping.

## Scraping Scope

This project will only scrape the first three catalogue pages and the book links found on those pages. It will not crawl the entire website.

## Data to Collect

The scraper will collect data such as:

* Title
* Book URL
* Price
* Description
* Rating
* Availability

## Robots.txt

When opening:

`https://books.toscrape.com/robots.txt`

it shows **404 NOT FOUND**.

I will not reuse this code on another site without checking its rules and terms first.

## Technology Stack
This project uses python lane.

| Technology     | Purpose                          |
| -------------- | -------------------------------- |
| Python 3.10+   | Main programming language        |
| Requests       | Sending HTTP requests            |
| Beautiful Soup | Parsing HTML and extracting data |
| Pydantic       | Validating scraped records       |
| JSON           | Storing structured output        |
| Git            | Version control                  |
| GitHub         | Publishing the project           |

## Project Structure

```text
scraper/
│
├── src/
│   └── main.py
│
├── cache/
│   ├── catalogue-page-1.html
│   ├── catalogue-page-2.html
│   ├── catalogue-page-3.html
│   └── ...
│
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
│
├── README.md
├── .gitignore
└── requirements.txt
```

### Folder and File Description

* `src/main.py` - Main scraper program.
* `cache/` - Stores downloaded HTML pages so repeated development runs do not repeatedly request the website.
* `output/books.json` - Contains the validated book records.
* `output/errors.json` - Contains invalid records or failures together with their reasons.
* `output/run-report.json` - Contains statistics about the scraper run.
* `README.md` - Project documentation and instructions.
* `.gitignore` - Prevents files such as cached HTML from being committed.
* `requirements.txt` - Lists the Python dependencies required by the project.

The assignment specifically requires cached HTML to be excluded from the published repository by adding `cache/` to `.gitignore`.

## Installation

Clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

Run the scraper with:

```bash
python src/main.py
```

The output files are created in the `output/` folder:

```text
output/
├── books.json
├── errors.json
└── run-report.json
```

## Record Schema

Each validated book record contains:

* `title` - Book title
* `product_url` - Absolute URL of the book page
* `price_text` - Original price text from the page
* `price_gbp` - Clean numeric price in GBP
* `availability_text` - Original availability text
* `rating_text` - Original rating text
* `description` - Book description, or `null` when unavailable
* `source_page` - Catalogue page where the book was discovered
* `fetched_at` - Time when the book page was fetched

Records are validated before being written to `books.json`. Invalid records are written to `errors.json` together with the reason for failure.

## Politeness Rules

The scraper follows these rules when making real requests:

* Uses an identifying User-Agent.
* Uses a request timeout.
* Waits at least 500 ms between real requests.
* Checks the HTTP status code before processing a response.
* Uses cached HTML during development to avoid repeatedly requesting the website.
* Does not retry a 404 or 403 response.
* Retries a timeout or 5xx server error once.

Cached pages do not require a delay because they are read from the local computer.

## Caching

Downloaded HTML pages are stored in the `cache/` directory.

The cache allows development runs to reuse previously downloaded pages instead of repeatedly requesting the website.

The `cache/` directory is ignored by Git and is not included as part of the published project.

## Validation and Duplicate Handling

Every scraped record is validated against the Pydantic schema before being stored.

Invalid records are not added to `books.json`. They are recorded in `errors.json` with the reason for failure.

The absolute `product_url` is used as the record identity, so duplicate book URLs are not stored more than once.

Running the scraper again should produce the same 60 unique records instead of creating duplicates.

## Failure Handling

Each book page is handled independently.

If one page fails, the scraper records the failure and continues processing the remaining pages.

A timeout or 5xx server error is retried once. A 404 or 403 response is not retried.

The scraper creates `run-report.json` at the end of each run so that failures and other run statistics are visible.

## Sample Run Report

A real run of the scraper produced the following report:

```json
{
  "pages_fetched": 0,
  "cache_hits": 63,
  "detail_pages": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

This run shows that 60 detail pages were processed and 60 valid records were produced.

## Why No Browser Is Needed

The core assignment does not need a browser because the required book data is already present in the HTML returned by the server. Using a browser would add unnecessary cost and complexity.

## Ethical Scraping

This project is limited to the public practice sandbox used for the assignment.

When scraping other websites:

* Use an official API when one exists.
* Never bypass logins.
* Never bypass paywalls.
* Never bypass blocks.
* Collect only the data that is needed.
* Check the site's rules and terms before reusing scraping code.

## Limitation

This scraper is designed for the HTML structure of Books to Scrape. If the site's page structure or selectors change, the scraper may need to be updated.

