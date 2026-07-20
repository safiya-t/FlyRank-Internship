from fastapi import FastAPI

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
    return {"error": "Task not found"}