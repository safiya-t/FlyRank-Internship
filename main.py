from fastapi import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Response
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
    if task.title == "":
        raise HTTPException(status_code=400, 
                            detail={"error": "Title cannot be empty"})
    
    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "done": task.done
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    for t in tasks:
        if t["id"] == task_id:
            if task.title == "":
                raise HTTPException(status_code=400, 
                                    detail={"error": "Title cannot be empty"})
            t["title"] = task.title
            t["done"] = task.done
            return t    
    raise HTTPException(status_code=404, detail={"error": "Task not found"})

@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    for t in tasks:
        if t["id"] == task_id:
            tasks.remove(t)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail={"error": "Task not found"})


    
     
        