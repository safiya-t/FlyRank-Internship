# Task API

A lightweight RESTful Task Management API built with **FastAPI**, **Pydantic**, and **PostgreSQL**. The API supports creating, reading, updating, and deleting tasks while storing data persistently in a PostgreSQL database running inside Docker.

---

## Features

| Feature | Description |
|---------|-------------|
| Task Management | Create, read, update, and delete tasks using RESTful API endpoints. |
| Persistent Data Storage | Stores task data permanently using PostgreSQL database. |
| Dockerized Database | PostgreSQL runs inside a Docker container for easy setup and deployment. |
| Docker Compose Support | Runs the FastAPI application and PostgreSQL database together using a single command. |
| Request Validation | Uses Pydantic models to validate incoming API request data. |
| Interactive API Documentation | Provides automatically generated Swagger UI and ReDoc documentation. |
| Task Filtering | Allows filtering tasks based on completion status and title. |
| Environment Configuration | Uses environment variables to securely manage database credentials and configuration. |
| Database Persistence | Maintains stored data even after restarting Docker containers using volumes. |
| Health Monitoring | Includes health check endpoint to verify API availability. |

---

## Technology Stack

* Python
* FastAPI
* Pydantic
* PostgreSQL
* Docker
* Docker Compose
* Psycopg
* Uvicorn

---

## Project Structure

```text
task-api/
├── main.py
├── database.py
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── screenshots/
    └── tasks database.png
```

---

## Running the Application

### 1. Create environment file

Copy `.env.example` and create `.env`

```powershell
cp .env.example .env
```

Example `.env`:

```env
DATABASE_URL=postgres://username:password@localhost:5432/tasks
```
---

### 2. Start the application using Docker Compose

```powershell
docker compose up
```

This starts:

* FastAPI application
* PostgreSQL database
* Database volume for persistent storage

---

### 3. Stop the application

```powershell
docker compose down
```

---

### 4. Open the API documentation

Swagger UI

```
http://127.0.0.1:8000/docs
```

ReDoc

```
http://127.0.0.1:8000/redoc
```

---

## API Endpoints

| Method | Endpoint           | Description             |
| ------ | ------------------ | ----------------------- |
| GET    | `/`                | Return API information  |
| GET    | `/health`          | Return health status    |
| GET    | `/tasks`           | Retrieve all tasks      |
| GET    | `/tasks/{task_id}` | Retrieve a task by ID   |
| POST   | `/tasks`           | Create a new task       |
| PUT    | `/tasks/{task_id}` | Update an existing task |
| DELETE | `/tasks/{task_id}` | Delete a task            |

---

## Example Request

### Create a Task

**Request**

```json
{
  "title": "Complete FastAPI Assignment"
}
```

**Response**

```json
{
  "id": 4,
  "title": "Complete FastAPI Assignment",
  "done": false
}
```

---

## Example curl Output

Retrieve all tasks:

```powershell
curl -i http://localhost:8000/tasks
```

Response:

```http
HTTP/1.1 200 OK
content-type: application/json

[
  {
    "id": 1,
    "title": "Learn FastAPI",
    "done": false
  },
  {
    "id": 2,
    "title": "Learn Docker",
    "done": false
  }
]
```

---

## PostgreSQL Database

The project uses a PostgreSQL database running inside a Docker container.

When the application starts for the first time:

* The PostgreSQL database is created automatically.
* The `tasks` table is created if it does not already exist.
* Sample tasks are inserted automatically.
* Data remains available after restarting containers because of Docker volume persistence.

Database table:

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL
);
```

Changes made through the API remain available after restarting the application.

---

## Example SQL Queries

Retrieve all tasks:

```sql
SELECT * FROM tasks;
```

Retrieve completed tasks:

```sql
SELECT * FROM tasks WHERE done = true;
```

Count all tasks:

```sql
SELECT COUNT(*) FROM tasks;
```

Update all tasks as completed:

```sql
UPDATE tasks
SET done = true;
```

Delete completed tasks:

```sql
DELETE FROM tasks
WHERE done = true;
```

---

## PostgreSQL Database Tools

Open PostgreSQL using:

```powershell
docker exec -it taskdb psql -U postgres -d tasks
```

Use PostgreSQL commands to:

* View stored records
* Execute SQL queries
* Verify database persistence

Example:

```sql
\dt

SELECT * FROM tasks;
```

(Add your PostgreSQL screenshot here.)

---

## Requirements

Install all dependencies using:

```powershell
pip install -r requirements.txt
```

`requirements.txt`

```
fastapi
uvicorn[standard]
psycopg[binary]
python-dotenv
```

---

## Environment Variables

The application uses `.env` for database configuration.

`.env.example`

```env
DATABASE_URL=postgres://username:password@db:5432/tasks
```

The `.env` file is ignored by Git and should not be committed.

---

## Notes

* Task data is stored persistently in PostgreSQL.
* PostgreSQL runs inside a Docker container.
* Docker Compose starts the complete application stack using one command.
* Database credentials are stored securely using environment variables.
* FastAPI automatically generates interactive API documentation.