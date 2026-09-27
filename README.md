# AI Image Understanding & Content Matching Engine

A backend API built with FastAPI, PostgreSQL, SQLAlchemy, and Google Gemini Flash & Embeddings for image analysis and semantic content matching.

---

## Project Structure

```text
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point, GET /health & GET /health/db
│   ├── config.py        # Settings & environment configuration (Pydantic)
│   ├── database.py      # SQLAlchemy engine, sessionmaker, Base & connection check
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── ai.py            # Gemini Flash & Embeddings integration
│   ├── matching.py      # Semantic similarity & vector matching logic
│   ├── guard.py         # Input validation & safety guardrails
│   └── routes.py        # API endpoint routes
├── images/              # Local storage for uploaded images
├── tests/               # Pytest suite
│   ├── __init__.py
│   ├── test_health.py   # Health endpoint tests
│   └── test_database.py # Database connection & health tests
├── .env.example         # Example environment variables template
├── .gitignore           # Git ignore file
├── check_db.py          # Standalone database connectivity check script
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## Setup & Installation

### 1. Create Virtual Environment

On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

Set your configuration values inside `.env`:
- `GEMINI_API_KEY`: Your Google Gemini API key.
- `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql://postgres:postgres@localhost:5432/image_matching_db`).

---

## Database Configuration & Connectivity Check

### 1. Create the Database in PostgreSQL

Using `psql` CLI:
```sql
CREATE DATABASE image_matching_db;
```

Or using Docker:
```powershell
docker run --name postgres-capstone -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=image_matching_db -p 5432:5432 -d postgres:16
```

### 2. Test Connection via Script

Run either of the following commands:
```powershell
python check_db.py
# or
python -m app.database
```

- If successful, it prints: `[OK] Database connection successful!`
- If it fails, it prints a clear error message along with a 4-step troubleshooting checklist.

---

## Running the Application

Start the FastAPI application using Uvicorn:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) (does not require DB or API key)
- **Database Health Check**: [http://127.0.0.1:8000/health/db](http://127.0.0.1:8000/health/db) (reports DB status and connection errors)
- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Tests

Run the test suite with pytest:

```powershell
pytest
```
