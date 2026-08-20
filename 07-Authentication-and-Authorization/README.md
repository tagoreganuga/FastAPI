# Authentication & Authorization

## Table of Contents

- [Why Split the App?](#why-split-the-app)
- [Routers - Scaling the Application](#routers---scaling-the-application)
- [One to Many Relationship](#one-to-many-relationship)
- [Foreign Keys](#foreign-keys)
- [Users Table Creation](#users-table-creation)
- [Create First User](#create-first-user)
- [Hash User's Password](#hash-users-password)
- [Save User to Database](#save-user-to-database)
- [Authenticate a User](#authenticate-a-user)
- [JWT Overview](#jwt-overview)
- [Encode a JWT](#encode-a-jwt)
- [Decode a JWT](#decode-a-jwt)
- [Authentication Enhancements](#authentication-enhancements)
- [Quick Revision Summary](#quick-revision-summary)

---

## Why Split the App?

As the application grows, mixing authentication logic with to-do logic in a single `main.py` file becomes messy and hard to maintain. We need a way to separate concerns.

### The Problem

Creating a new `auth.py` file with its own `app = FastAPI()` means it runs as a **separate application** - requiring its own port (`uvicorn auth:app`). You can't access both to-do and auth endpoints at the same URL.

### The Solution

Use **routers** to combine multiple files into one application running on a single port.

---

## Routers - Scaling the Application

### What is a Router?

A router lets `main.py` act as the root, with different route files (like `auth.py` and `todos.py`) connected to it. Each file holds its own API endpoints but they all run on the same FastAPI app.

### Step 1 - Create a `routers` Package

```
TodoApp/
├── main.py
├── models.py
├── database.py
└── routers/
    ├── __init__.py
    ├── auth.py
    └── todos.py
```

### Step 2 - Convert `auth.py` to Use APIRouter

```python
# routers/auth.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_user():
    return {"user": "authenticated"}
```

| Before (standalone app) | After (router) |
|--------------------------|----------------|
| `from fastapi import FastAPI` | `from fastapi import APIRouter` |
| `app = FastAPI()` | `router = APIRouter()` |
| `@app.get(...)` | `@router.get(...)` |

### Step 3 - Convert `todos.py` the Same Way

Copy all to-do endpoints from `main.py` into `routers/todos.py`, change `app` to `router`, and remove database-creation code (that stays in `main.py`).

### Step 4 - Include Routers in `main.py`

```python
# main.py
from fastapi import FastAPI
from database import engine
import models
from routers import auth, todos

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)
```

### Result

Running `uvicorn main:app --reload` shows **all endpoints** from both `auth.py` and `todos.py` in the Swagger UI - all on one port.

---

## One to Many Relationship

### The Concept

A single **user** can have multiple **to-dos**, but a to-do belongs to only one user.

```
User (1) ──────< (many) To-Dos
```

- User "tagore" can have: take out garbage, get a haircut, take a shower
- Multiple users can exist, each with their own group of to-dos

### Two Tables

| Users Table | To-Dos Table |
|-------------|--------------|
| id (PK) | id (PK) |
| email | title |
| username | description |
| first_name | priority |
| last_name | complete |
| hashed_password | **owner_id (FK)** |
| is_active | |
| role | |

The **owner_id** column on the to-dos table links each to-do back to a specific user.

---

## Foreign Keys

### What is a Foreign Key?

A **foreign key (FK)** is a column in one table that references the **primary key** of another table. It creates a link between the two tables.

```
To-Dos Table                     Users Table
┌────┬───────┬──────────┬─────────┐    ┌────┬───────┬──────┐
│ id │ title │ priority │ owner_id│    │ id │ email │ ...  │
├────┼───────┼──────────┼─────────┤    ├────┼───────┼──────┤
│ 1  │ ...   │ 5        │ 1       │───>│ 1  │ ...   │ ...  │
│ 2  │ ...   │ 3        │ 1       │/   │    │       │      │
│ 3  │ ...   │ 2        │ 2       │───>│ 2  │ ...   │ ...  │
└────┴───────┴──────────┴─────────┘    └────┴───────┴──────┘
```

- To-dos with `owner_id = 1` belong to user with `id = 1`
- To-dos with `owner_id = 2` belong to user with `id = 2`

### Querying with Foreign Keys

```sql
-- All to-dos for user 1
SELECT * FROM todos WHERE owner = 1;

-- All to-dos for user 2
SELECT * FROM todos WHERE owner = 2;
```

> **Note:** We don't need a foreign key on the users table because the relationship is one-way: we only look up to-dos **by** user, not users by to-do.

---

## Users Table Creation

> **Important:** SQLAlchemy can only **create** tables, not enhance existing ones. To add new columns, delete the old `.db` file and let the app recreate it. (Alembic handles migrations later.)

### Add the Users Model

```python
# models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
```

### Add Foreign Key to To-Dos

```python
class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
```

### What is Password Hashing?

Hashing converts a password into a scrambled string that **cannot be reversed**. When a user logs in, we hash their input and compare it to the stored hash - we never see or store the original password.

```
"test1234"  ──hash──>  "$2b$12$N9o..."  (stored in DB)

Login: "test1234" ──hash──> compare with stored hash
```

- Developers can't see user passwords
- If the database is leaked, passwords remain protected

---

## Create First User

### Pydantic Request Model

```python
# routers/auth.py
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
```

### Why No `id` or `is_active` in the Request?

| Field | Why It's Excluded |
|-------|-------------------|
| `id` | Auto-incremented by the database |
| `is_active` | Defaults to `True` for every new user |
| `hashed_password` | The request has `password`; we hash it before saving |

### The POST Endpoint

```python
@router.post("/")
async def create_user(create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=create_user_request.password,  # plain text (for now)
        is_active=True
    )
    return create_user_model
```

### Why Not Use `**model_dump()`?

The request has `password` but the model has `hashed_password` - the field names don't match, so the dictionary unpacking trick doesn't work. We must map each field manually.

---

## Hash User's Password

### Install Dependencies

```bash
pip install passlib
pip install bcrypt==4.0.1
```

> **Warning:** You must install `bcrypt==4.0.1` exactly. Other versions break passlib with an `__about__` error.

### Set Up Bcrypt Context

```python
# routers/auth.py
from passlib.context import CryptoContext

bcrypt_context = CryptoContext(schemes=["bcrypt"], deprecated="auto")
```

### Hash the Password

```python
hashed_password = bcrypt_context.hash(create_user_request.password)
```

| Before Hashing | After Hashing |
|----------------|---------------|
| `test1234` | `$2b$12$N9o...` (long scrambled string) |

### How Verification Works

We never "de-hash" a password. Instead, we hash the login input and compare:

```python
bcrypt_context.verify(plain_password, hashed_password)  # returns True or False
```

---

## Save User to Database

### Add Database Dependency to `auth.py`

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
```

### Update the POST Endpoint

```python
from starlette import status

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
```

### Verify in SQLite

```bash
sqlite3 todosapp.db
SELECT * FROM users;
```

You'll see the user with a hashed password, `is_active = 1` (true), and their role.

---

## Authenticate a User

### The Login Endpoint

```python
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    return "token"
```

### What is `OAuth2PasswordRequestForm`?

A special form type that provides a **username** and **password** field (plus optional fields like `grant_type`, `scope`). It appears in Swagger UI as a login form.

Install it first:

```bash
pip install python-multipart
```

### The `authenticate_user` Function

```python
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user
```

### Authentication Flow

```bsh
1. User submits username + password
         ↓
2. Query database for user by username
         ↓
3. User not found? → return False
         ↓
4. bcrypt_context.verify(password, user.hashed_password)
         ↓
5. Password mismatch? → return False
         ↓
6. Return the user object (success)
```

### Using It in the Endpoint

```python
@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        return "failed authentication"
    return "successful authentication"
```

### Testing in Swagger

| Input | Result |
|-------|--------|
| Wrong username + wrong password | Failed authentication |
| Correct username + wrong password | Failed authentication |
| Correct username + correct password | Successful authentication |

---

## JWT Overview

### What is a JWT?

A **JSON Web Token (JWT)** is a self-contained, digitally signed string that securely transmits information between client and server. It allows a user to stay logged in without re-authenticating on every request.

### JWT Structure

A JWT has **three parts** separated by dots:

```
aaaaaaa.bbbbbbbb.cccccccc
  │        │        │
  │        │        └── Signature
  │        └───── Payload
  └──────────── Header
```

### The Three Parts

| Part | Contents | Encoding |
|------|----------|----------|
| **Header** | Algorithm (e.g., HS256) + token type (JWT) | Base64 |
| **Payload** | User data + claims (sub, id, exp) | Base64 |
| **Signature** | Hash of encoded header + payload + secret | Hashed |

### Payload Claims

| Claim | Full Name | Purpose |
|-------|-----------|---------|
| `iss` | Issuer | Who issued the token |
| `sub` | Subject | Unique identifier (e.g., username) |
| `exp` | Expiration | When the token becomes invalid |

> **Important:** Always set an expiration time. A token that never expires means anyone who captures it is authorized forever.

### How It Works

```
1. User logs in → server returns a JWT
2. Client stores the JWT
3. Each request → client sends JWT in the Authorization header
4. Server validates the JWT signature using the secret key
5. If valid → process the request
```

### The Secret Key

The secret is stored **only on the server**. If a client discovers it, they can forge valid tokens. This is why it must stay private.

### Security Note

JWTs are safe as long as the secret key is not leaked. The server can detect tampering because the signature won't match if any part of the token is altered.

### JWT Encoder/Decoder
Visit [https://jwt.io/](https://jwt.io/) to encode and decode JWTs.

---

## Encode a JWT

### Install the JWT Library

```bash
pip install "python-jose[cryptography]"
```

### Set Up Secret Key and Algorithm

```python
from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
ALGORITHM = "HS256"
```

Generate a random secret with:

```bash
openssl rand hex 32
```

### Create the Access Token Function

```python
def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Breakdown

| Piece | Purpose |
|-------|---------|
| `encode` dictionary | The payload - holds `sub` (username) and `id` |
| `expire` | Current UTC time + the expiration duration |
| `encode.update({"exp": expire})` | Adds the expiration claim to the payload |
| `jwt.encode(...)` | Encodes payload + secret + algorithm into the JWT string |

> **Note:** `datetime.utcnow()` is deprecated. Use `datetime.now(timezone.utc)` instead, and import `timezone` from `datetime`.

### The Token Response Model

```python
class Token(BaseModel):
    access_token: str
    token_type: str
```

### Update the Login Endpoint

```python
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate user")
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}
```

### Testing

1. POST `/auth/token` with correct username + password
2. Response contains `access_token` (the JWT string) and `token_type: "bearer"`
3. Paste the token at [jwt.io](https://jwt.io/) to see the decoded header, payload, and expiration

---

## Decode a JWT

### Why Decode?

Every secured endpoint must verify the incoming JWT to confirm the user is authorized. Decoding checks the signature using the *Secret Key*.

### Set Up OAuth2 Bearer

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")
```

`tokenUrl` tells Swagger where the login endpoint is, so it knows where to send credentials to get a token.

### The `get_current_user` Function

```python
from jose import jwt, JWTError
from fastapi import HTTPException, status

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")

        return {"username": username, "id": user_id}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")
```

### Decoding Flow

```
1. Client sends JWT in the Authorization header (Bearer schema)
         ↓
2. oauth2_bearer extracts the token
         ↓
3. jwt.decode(token, SECRET_KEY, algorithm) verifies the signature
         ↓
4. Extract username and user_id from the payload
         ↓
5. Missing username or id? → 401 Unauthorized
         ↓
6. JWTError (invalid/tampered token)? → 401 Unauthorized
         ↓
7. Return {"username": ..., "id": ...} for the endpoint to use
```

> **Note:** This is **not an API endpoint** - it's a dependency that other endpoints will use to verify the current user before processing their request.

---

## Authentication Enhancements

### 1 - Return Proper HTTP Exceptions on Login Failure

Replace the string `"failed authentication"` with a proper 401 error:

```python
if not user:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user"
    )
```

### 2 - Add Prefix and Tags to the Router

```python
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
```

| Setting | Effect |
|---------|--------|
| `prefix="/auth"` | All endpoints in this file start with `/auth` |
| `tags=["auth"]` | Swagger UI groups these endpoints under an "auth" heading |

### 3 - Clean Up Redundant Paths

Since the prefix is already `/auth`, remove the redundant `/auth` from individual routes:

| Before | After |
|--------|-------|
| `@router.post("/auth/")` | `@router.post("/")` → becomes `/auth` |
| `@router.post("/token")` | `@router.post("/token")` → becomes `/auth/token` |

### 4 - Update the `tokenUrl` to Match

```python
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
```

This ensures Swagger knows the correct login endpoint path after adding the prefix.

### Result in Swagger UI

```
auth
├── POST /auth          (create user)
└── POST /auth/token    (login → get JWT)

todos
├── GET  /
├── GET  /todo/{todo_id}
├── POST /todo
├── PUT  /todo/{todo_id}
└── DELETE /todo/{todo_id}
```

---

## Quick Revision Summary

### Key Concepts

| Concept | One-Line Summary |
|---------|-----------------|
| **Routers** | Split endpoints into separate files, all mounted on one app via `include_router()` |
| **One to Many** | One user owns many to-dos; each to-do has one owner |
| **Foreign Key** | `owner_id` on the to-dos table references `users.id` |
| **Password Hashing** | Use `passlib` + `bcrypt==4.0.1` to hash passwords; verify with `bcrypt_context.verify()` |
| **Authentication** | Verify username + password against the database |
| **JWT** | A signed token (header.payload.signature) carrying user info with an expiration |
| **Encode JWT** | `jwt.encode(payload, SECRET_KEY, algorithm)` - creates the token |
| **Decode JWT** | `jwt.decode(token, SECRET_KEY, algorithm)` - verifies and reads the token |
| **OAuth2 Bearer** | Dependency that extracts the JWT from the Authorization header |
