from fastapi import HTTPException, Header,FastAPI
from pydantic import BaseModel
from fastapi import Response, status
from database import get_connection, init_db, supabase

app = FastAPI(
    title="Task API",
    description=" A CRUD REST API built with FastAPI and PostgreSQL for managing tasks."
)

@app.on_event("startup")
async def startup():
          init_db()

class Task(BaseModel):
    title: str
    done: bool


##
@app.get("/")
async def root():
    return {"message": "Hello World"}
##
@app.get("/health")
async def health():
    return {"status": "healthy"}
##
@app.get("/tasks")
async def get_tasks( done: bool = None, title: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT id, title, done FROM tasks"
    params = []
    
    conditions = []

    if done is not None:
       conditions.append("done = %s")
       params.append(done)

    if title:
       conditions.append("title ILIKE %s")
       params.append(f"%{title}%")

    if conditions:
       query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    conn.close() 
    return [
    {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }
    for row in rows
 ] 
##
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
    "SELECT id, title, done FROM tasks WHERE id = %s",
    (task_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
    "id": row[0],
    "title": row[1],
    "done": row[2]
    }
 ##   
@app.post("/tasks", status_code=201)
async def create_task(task: Task):

    conn = get_connection()
    
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks(title, done)
        VALUES(%s, %s)
        RETURNING id, title, done;
        """,
        (task.title, task.done)
    )

    new_task = cursor.fetchone()

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": new_task[0],
        "title": new_task[1],
        "done": new_task[2]
    }
##
@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: Task):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title=%s,
            done=%s
        WHERE id=%s
        RETURNING id, title, done;
        """,
        (
            updated_task.title,
            updated_task.done,
            task_id
        )
    )


    updated_task = cursor.fetchone()


    if updated_task is None:
        cursor.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )


    conn.commit()

    cursor.close()
    conn.close()


    return {
        "id": updated_task[0],
        "title": updated_task[1],
        "done": updated_task[2]
     }
##
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM tasks
        WHERE id=%s
        RETURNING id;
        """,
        (task_id,)
    )

    deleted = cursor.fetchone()

    if deleted is None:

        cursor.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    conn.commit()
    cursor.close()
    conn.close()

    return
    
##Auth and signup
class AuthRequest(BaseModel):
    email: str
    password: str          

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(data: AuthRequest):

    print("EMAIL RECEIVED:", repr(data.email), flush=True)

    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "user": response.user.model_dump() if response.user else None
        }

    except Exception as e:
     print("SUPABASE ERROR:", repr(e), flush=True)
     raise HTTPException(
        status_code=400,
        detail=str(e)
    )
##
@app.post("/auth/login")
def login(data: AuthRequest):
    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not response.session:
            raise HTTPException(
                status_code=401,
                detail={"error": "Invalid login credentials"}
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid login credentials"}
        )

@app.get("/public/info")
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }

@app.get("/protected/profile")
def protected_profile(authorization: str | None = Header(default=None, alias="Authorization")):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    token = authorization.split(" ", 1)[1]

    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    try:
        response = supabase.auth.get_user(token)
        user = response.user

    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid or expired token"}
        )

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }      