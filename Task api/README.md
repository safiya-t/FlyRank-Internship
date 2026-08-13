# Task API

A lightweight RESTful Task Management API built with **FastAPI**, **Pydantic**, **PostgreSQL**, and **Supabase Authentication**. The API supports creating, reading, updating, and deleting tasks while storing data persistently in a PostgreSQL database running inside Docker.

The API also provides **user authentication using Supabase Auth**, including user signup, login, logout, JWT access-token verification, and protected routes. FastAPI's dependency-based security system is used to protect authenticated endpoints, and Swagger UI provides interactive testing with Bearer token authentication.

---

## Features

| Feature                       | Description                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| Task Management               | Create, read, update, and delete tasks using RESTful API endpoints.                   |
| Persistent Data Storage       | Stores task data permanently using PostgreSQL database.                               |
| Dockerized Database           | PostgreSQL runs inside a Docker container for easy setup and deployment.              |
| Docker Compose Support        | Runs the FastAPI application and PostgreSQL database together using a single command. |
| Request Validation            | Uses Pydantic models to validate incoming API request data.                           |
| Interactive API Documentation | Provides automatically generated Swagger UI and ReDoc documentation.                  |
| Task Filtering                | Allows filtering tasks based on completion status and title.                          |
| Environment Configuration     | Uses environment variables to securely manage database credentials and configuration. |
| Database Persistence          | Maintains stored data even after restarting Docker containers using volumes.          |
| Health Monitoring             | Includes health check endpoint to verify API availability.                            |
| User Signup                   | Allows users to create accounts using Supabase Authentication.                        |
| User Login                    | Authenticates users and returns a JWT access token and refresh token.                 |
| JWT Verification              | Verifies access tokens with Supabase before allowing access to protected routes.      |
| Protected Routes              | Restricts selected API endpoints to authenticated users.                              |
| Authentication Dependency     | Uses a reusable FastAPI dependency to verify authenticated users.                     |
| User Logout                   | Allows authenticated users to log out through Supabase Auth.                          |
| Bearer Authentication         | Uses `Authorization: Bearer <token>` for protected API requests.                      |
| Swagger Bearer Authorization  | Swagger UI provides an **Authorize** button for testing protected endpoints.          |

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
* Supabase
* Supabase Auth
* JWT
* python-dotenv

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
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

The `SUPABASE_KEY` should be the **anon key** from the Supabase project. The `service_role` key should never be placed in the application configuration for this assignment.

---

### 2. Start the application using Docker Compose

```powershell
docker compose up
```

This starts:

* FastAPI application
* PostgreSQL database
* Database volume for persistent storage

The FastAPI server is available at:

```text
http://127.0.0.1:8000
```

---

### 3. Stop the application

```powershell
docker compose down
```

---

### 4. Open the API documentation

Swagger UI

```text
http://127.0.0.1:8000/docs
```

ReDoc

```text
http://127.0.0.1:8000/redoc
```

Swagger UI can also be used to test authenticated endpoints by clicking **Authorize** and providing a valid JWT access token.

---

## API Endpoints

| Method | Endpoint               | Description                         | Authentication |
| ------ | ---------------------- | ----------------------------------- | -------------- |
| GET    | `/`                    | Return API information              | No             |
| GET    | `/health`              | Return health status                | No             |
| GET    | `/tasks`               | Retrieve all tasks                  | No             |
| GET    | `/tasks/{task_id}`     | Retrieve a task by ID               | No             |
| POST   | `/tasks`               | Create a new task                   | No             |
| PUT    | `/tasks/{task_id}`     | Update an existing task             | No             |
| DELETE | `/tasks/{task_id}`     | Delete a task                       | No             |
| POST   | `/auth/signup`         | Create a new user account           | No             |
| POST   | `/auth/login`          | Authenticate user and return tokens | No             |
| POST   | `/auth/logout`         | Log out the authenticated user      | Yes            |
| GET    | `/public/info`         | Return public information           | No             |
| GET    | `/protected/profile`   | Return authenticated user details   | Yes            |
| GET    | `/protected/dashboard` | Return protected dashboard data     | Yes            |

Protected endpoints require:

```text
Authorization: Bearer <access_token>
```

---

## Authentication

The API uses **Supabase Auth** as the Identity Provider.

The authentication flow is:

```text
Client
   |
   | Email + Password
   v
Supabase Auth
   |
   | JWT Access Token
   v
Client
   |
   | Authorization: Bearer <JWT>
   v
FastAPI
   |
   | Verify token
   v
Supabase
   |
   | Valid / Invalid
   v
Protected Route
```

The application does not store or hash user passwords itself. Supabase Auth manages user accounts, passwords, and authentication tokens.

---

### User Signup

Create a new account using:

```http
POST /auth/signup
```

Request:

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

Successful signup returns:

```text
201 Created
```

Missing email or password returns:

```text
400 Bad Request
```

---

### User Login

Authenticate an existing user using:

```http
POST /auth/login
```

Request:

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

A successful login returns an access token and refresh token.

Example:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "..."
}
```

The `access_token` is the JWT used to access protected endpoints.

Invalid login credentials return:

```text
401 Unauthorized
```

---

### Bearer Token Authentication

Protected endpoints require the JWT in the HTTP `Authorization` header.

Example:

```http
Authorization: Bearer eyJhbGciOi...
```

The FastAPI authentication dependency:

1. Reads the `Authorization` header.
2. Checks that it uses the `Bearer` scheme.
3. Extracts the access token.
4. Sends the token to Supabase for verification.
5. Rejects invalid or expired tokens.
6. Allows the request to continue when the token is valid.

---

### Protected Profile

```http
GET /protected/profile
```

This endpoint can only be accessed with a valid JWT.

Example:

```powershell
curl -i http://localhost:8000/protected/profile `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

A valid token returns:

```text
200 OK
```

An absent, malformed, invalid, or expired token returns:

```text
401 Unauthorized
```

---

### Protected Dashboard

```http
GET /protected/dashboard
```

This endpoint uses the **same authentication dependency** as `/protected/profile`.

This demonstrates that authentication logic is reusable instead of being duplicated inside every protected route.

---

### Logout

```http
POST /auth/logout
```

Logout is a protected operation and requires the access token.

Example:

```powershell
curl -i -X POST http://localhost:8000/auth/logout `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Successful logout returns:

```text
204 No Content
```

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

### Authentication Testing with curl

#### Signup

```powershell
$body = @{
    email = "test@example.com"
    password = "password123"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/auth/signup" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

#### Login

```powershell
$body = @{
    email = "test@example.com"
    password = "password123"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

Copy the `access_token` returned by the login request.

#### Access Protected Profile

```powershell
curl -i http://127.0.0.1:8000/protected/profile `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

A valid token should return:

```text
200 OK
```

Testing without a token:

```powershell
curl -i http://127.0.0.1:8000/protected/profile
```

should return:

```text
401 Unauthorized
```

Testing with a modified token should also return:

```text
401 Unauthorized
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

```text
fastapi
uvicorn[standard]
psycopg[binary]
python-dotenv
supabase
```

---

## Environment Variables

The application uses `.env` for database and Supabase authentication configuration.

`.env.example`

```env
DATABASE_URL=postgres://username:password@db:5432/tasks
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

The `.env` file is ignored by Git and should not be committed.

The Supabase configuration contains credentials required for authentication. Only the **anon key** should be used for this application. Do not expose or commit the Supabase `service_role` key.

---

## Swagger Authentication

FastAPI automatically generates Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

The protected endpoints are configured with HTTP Bearer authentication.

To test them:

1. Open `/docs`.
2. Click **Authorize**.
3. Enter the JWT access token obtained from `/auth/login`.
4. Click **Authorize**.
5. Close the authorization window.
6. Open `GET /protected/profile`.
7. Click **Try it out**.
8. Click **Execute**.

Swagger automatically sends:

```http
Authorization: Bearer <access_token>
```

with the request.

A valid token should return:

```text
200 OK
```

An invalid or expired token should return:

```text
401 Unauthorized
```
---

## Authentication Status Codes

| Status Code | Meaning                                                          |
| ----------- | ---------------------------------------------------------------- |
| `200`       | Request successful                                               |
| `201`       | User account successfully created                                |
| `204`       | Logout successful with no response body                          |
| `400`       | Missing or invalid request input                                 |
| `401`       | Missing, malformed, invalid, or expired authentication token     |
| `403`       | Authenticated user does not have permission to access a resource |


---

                    ┌──────────────┐
                    │    Client    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    └──────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Authentication   Task API      Health
             │             │             │
             ▼             ▼             ▼
         Supabase      PostgreSQL     /health
           Auth          Docker
             │             │
             ▼             ▼
           JWT          Task Data
             │
             ▼
       Auth Dependency
             │
             ▼
      Protected Routes