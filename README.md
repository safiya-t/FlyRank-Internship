# Task API

A lightweight RESTful Task Management API built with **FastAPI**, **Pydantic**, and **SQLite**. The API supports creating, reading, updating, and deleting tasks while storing data persistently in a SQLite database.

<img width="1583" height="930" alt="Swagger UI Screenshot" src="https://github.com/user-attachments/assets/abc8ac19-3d30-402c-b832-7213a7834efe" />

---

## Features

* Create, read, update, and delete tasks
* Persistent data storage using SQLite
* Request validation with Pydantic
* Interactive API documentation with Swagger UI and ReDoc
* Filter tasks by completion status and title

---

## Technology Stack

* Python
* FastAPI
* Pydantic
* SQLite
* Uvicorn

---

## Project Structure

```text
task-api/
├── main.py
├── database.py
├── tasks.db
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Running the Application

### 1. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start the server

```powershell
uvicorn main:app --reload
```

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
| DELETE | `/tasks/{task_id}` | Delete a task           |

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

## SQLite Database

The project uses a SQLite database named `tasks.db`.

When the application starts for the first time:

* The database is created automatically.
* The `tasks` table is created if it does not already exist.
* Sample tasks are inserted automatically.

Changes made through the API remain available after restarting the server.

![alt text](<tasks database.png>)
---

## Example SQL Queries

Retrieve all tasks:

```sql
SELECT * FROM tasks;
```

Retrieve completed tasks:

```sql
SELECT * FROM tasks WHERE done = 1;
```

Count all tasks:

```sql
SELECT COUNT(*) FROM tasks;
```

Update all tasks as completed:

```sql
UPDATE tasks
SET done = 1;
```

Delete completed tasks:

```sql
DELETE FROM tasks
WHERE done = 1;
```

---

## DB Browser for SQLite

Open `tasks.db` using **DB Browser for SQLite** to:

* View stored records
* Execute SQL queries
* Edit task data directly
* Verify database persistence

(Add your DB Browser screenshot here.)

---

## Requirements

Install all dependencies using:

```powershell
pip install -r requirements.txt
```

---

## Notes

* Task data is stored persistently in SQLite.
* `tasks.db` is created automatically when the application is started.
* FastAPI automatically generates interactive API documentation.
