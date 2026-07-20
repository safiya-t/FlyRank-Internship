from fastapi import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Response

app = FastAPI()

tasks = [
    { "id": 1, "title": "Buy groceries", "done": False },
    { "id": 2, "title": "complete assignments", "done": True },
    { "id": 3, "title": "practice DSA", "done": False }
]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/tasks")
async def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
        raise HTTPException(status_code=404,
                             detail={"error": "Task not found"})
    
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


    
     
        