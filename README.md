# Task API

A lightweight RESTful Task Management API built with **FastAPI** and **Pydantic**. This project provides CRUD operations for tasks using an in-memory data store and exposes interactive API documentation through Swagger UI.

---

## Features

- Create, read, update, and delete tasks
- Request validation with Pydantic
- FastAPI-generated Swagger UI and ReDoc documentation
- Simple in-memory storage for quick local testing

---

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Pydantic

---

## Project Structure

```text
task-api/
¦
+-- main.py
+-- database.py
+-- requirements.txt
+-- README.md
+-- .gitignore
```

---

## Running the Application

1. Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the server:

```powershell
uvicorn main:app --reload
```
```

4. Open Swagger UI:

`http://127.0.0.1:8000/docs`

5. Open ReDoc:

`http://127.0.0.1:8000/redoc`

---

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/` | Return API information |
| GET | `/health` | Return health status |
| GET | `/tasks` | Retrieve all tasks |
| GET | `/tasks/{task_id}` | Retrieve a task by ID |
| POST | `/tasks` | Create a new task |
| PUT | `/tasks/{task_id}` | Update an existing task |
| DELETE | `/tasks/{task_id}` | Delete a task |

---

## Example Request

### Create a Task

**Request Body**

```json
{
  "title": "Complete FastAPI Assignment",
  "done": false
}
```

### Example Response

```json
{
  "id": 4,
  "title": "Complete FastAPI Assignment",
  "done": false
}
```

---

## Notes

- This application uses an in-memory list. Data is reset when the server restarts.
- The `requirements.txt` file includes the packages required to run the API locally.
