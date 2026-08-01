from fastapi import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Response, status
from database import get_connection, init_db

app = FastAPI()

tasks = [
    { "id": 1, "title": "Buy groceries", "done": False },
    { "id": 2, "title": "complete assignments", "done": True },
    { "id": 3, "title": "practice DSA", "done": False }
]

@app.on_event("startup")
async def startup():
          init_db()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/tasks")
async def get_tasks( done: bool = None, title: str = None):
    conn = get_connection()

    query = "SELECT * FROM tasks"
    params = []

    conditions = []

    if done is not None:
        conditions.append("done = ?")
        params.append(int(done))

    if title:
        conditions.append("title LIKE ?")
        params.append(f"%{title}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    rows = conn.execute(query, params).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
        for row in rows
    ]
    return tasks

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }
    
    
    
class Task(BaseModel):
    title: str
    done: bool

@app.post("/tasks", status_code=201)
async def create_task(task: Task):
    if task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks(title, done) VALUES (?, ?)",
        (task.title, 0)
    )

    conn.commit()

    task_id = cursor.lastrowid

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }

@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: Task):

    conn = get_connection()

    existing = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    if existing is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (
            updated_task.title,
            int(updated_task.done),
            task_id
        )
    )

    conn.commit()

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):

    conn = get_connection()

    existing = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    if existing is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


    
     
        