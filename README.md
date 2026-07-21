# Task API

A lightweight RESTful Task Management API built using **FastAPI**. The application provides CRUD (Create, Read, Update, Delete) functionality for managing tasks and follows REST architecture principles.

---
<img width="1583" height="930" alt="Screenshot 2026-07-21 203808" src="https://github.com/user-attachments/assets/c460fa9a-3ae6-4f09-af95-bc3f0de838e4" />


# Overview

The **Task API** is designed to manage a simple to-do list using an in-memory Python list. Since no database is used, all data is reset whenever the server restarts. The API uses **Pydantic** for request validation and automatically generates interactive API documentation through **Swagger UI**.

Each task contains the following fields:

| Field     | Description                                            |
| --------- | ------------------------------------------------------ |
| **ID**    | Unique identifier for each task                        |
| **Title** | Name or description of the task                        |
| **Done**  | Boolean value indicating whether the task is completed |

---

# Features

| Feature               | Description                                        |
| --------------------- | -------------------------------------------------- |
| RESTful API           | Implements CRUD operations using HTTP methods      |
| Create Tasks          | Add new tasks                                      |
| Read Tasks            | Retrieve all tasks or a specific task              |
| Update Tasks          | Modify an existing task                            |
| Delete Tasks          | Remove tasks from the list                         |
| Request Validation    | Validates incoming request data using Pydantic     |
| Error Handling        | Returns appropriate HTTP status codes and messages |
| Swagger Documentation | Interactive API documentation and testing          |
| In-Memory Storage     | Stores tasks in a Python list without a database   |

---

# Technology Stack

| Technology | Purpose              |
| ---------- | -------------------- |
| Python     | Programming language |
| FastAPI    | Backend framework    |
| Uvicorn    | ASGI server          |
| Pydantic   | Request validation   |

---

# Project Structure

```text
task-api/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Running the Application

Follow these steps to run the project locally.

| Step                                | Command / Action                       |
| ----------------------------------- | -------------------------------------- |
| **1. Activate Virtual Environment** | `.\.venv\Scripts\Activate.ps1`         |
| **2. Install Dependencies**         | `pip install fastapi uvicorn pydantic` |
| **3. Start the Server**             | `uvicorn main:app --reload`            |
| **4. Open Swagger UI**              | `http://127.0.0.1:8000/docs`           |
| **5. Open ReDoc**                   | `http://127.0.0.1:8000/redoc`          |

### Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```powershell
pip install fastapi uvicorn pydantic
```

### Start the Server

```powershell
uvicorn main:app --reload
```

### API Documentation

| Documentation | URL                           |
| ------------- | ----------------------------- |
| Swagger UI    | `http://127.0.0.1:8000/docs`  |
| ReDoc         | `http://127.0.0.1:8000/redoc` |

---

# API Endpoints

| Method | Endpoint      | Description                                  |
| :----: | ------------- | -------------------------------------------- |
|   GET  | `/`           | Returns API information                      |
|   GET  | `/health`     | Returns the health status of the application |
|   GET  | `/tasks`      | Retrieves all tasks                          |
|   GET  | `/tasks/{id}` | Retrieves a task by its ID                   |
|  POST  | `/tasks`      | Creates a new task                           |
|   PUT  | `/tasks/{id}` | Updates an existing task                     |
| DELETE | `/tasks/{id}` | Deletes a task                               |

---

# Example Requests

### Create a Task

**Request Body**

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

### Update a Task

**Request Body**

```json
{
  "title": "Submit Assignment",
  "done": true
}
```

**Response**

```json
{
  "id": 1,
  "title": "Submit Assignment",
  "done": true
}
```

---

### Get All Tasks

**Response**

```json
[
  {
    "id": 1,
    "title": "Study FastAPI",
    "done": false
  },
  {
    "id": 2,
    "title": "Complete Assignment",
    "done": true
  }
]
```

---

### Get Task by ID

**Response**

```json
{
  "id": 1,
  "title": "Study FastAPI",
  "done": false
}
```

---

### Delete a Task

**Response**

```
204 No Content
```

---

# Application Flow

```text
                     User / Client
                          │
                          ▼
                   HTTP Request
                          │
                          ▼
               FastAPI Application
                    (main.py)
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   Validate Request   Process Request   Find Task
      (Pydantic)                         by ID
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                 In-Memory Task List
           (Create • Read • Update • Delete)
                          │
                          ▼
                   HTTP Response
                          │
                          ▼
               Browser / Swagger UI
```
