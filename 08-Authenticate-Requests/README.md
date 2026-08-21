# Authenticate Requests

## Table of Contents

- [Overview](#overview)
- [User Dependency](#user-dependency)
- [POST Todo (User ID)](#post-todo-user-id)
- [Get All Todos (User ID)](#get-all-todos-user-id)
- [Get Todo by ID (User ID)](#get-todo-by-id-user-id)
- [PUT Todo (User ID)](#put-todo-user-id)
- [DELETE Todo (User ID)](#delete-todo-user-id)
- [Admin Router - Adding Role to JWT](#admin-router---adding-role-to-jwt)
- [Admin Endpoints](#admin-endpoints)

---

## Overview

Now that the JWT encode/decode flow is working, every to-do endpoint is locked behind authentication. Each request must include a valid JWT, and the server extracts the user from it so to-dos are scoped to their owner. An **admin router** is also added for role-based access control.

### What Changes

| Before | After |
|--------|-------|
| Any client can create/read/update/delete to-dos | Must be logged in (valid JWT) |
| All to-dos visible to everyone | Only the owner's to-dos are returned |
| No admin controls | Admin router can view/delete anyone's to-dos |

### Authentication Flow Per Request

```
1. Client sends JWT in Authorization header (Bearer token)
         ↓
2. get_current_user decodes the JWT → returns {username, id, role}
         ↓
3. Endpoint checks: if user is None → 401 Authentication failed
         ↓
4. Query the database filtered by owner_id = user["id"]
         ↓
5. Return, update, or delete only the matching records
```

---

## User Dependency

### Import `get_current_user` into `todos.py`

```python
# routers/todos.py
from .auth import get_current_user
from typing import Annotated
from fastapi import Depends

user_dependency = Annotated[dict, Depends(get_current_user)]
```

The `get_current_user` function (defined in `auth.py`) decodes the JWT and returns a dictionary with `username`, `id`, and `role`.

### The Standard Auth Check

Every protected endpoint starts with this guard:

```python
if user is None:
    raise HTTPException(status_code=401, detail="Authentication failed")
```

### Authorizing in Swagger

1. Click the **lock icon** on any protected endpoint
2. Enter username and password (e.g., `tagore` / `test1234`)
3. Click **Authorize** - Swagger automatically calls `/auth/token` and stores the JWT
4. The session stays authorized across all endpoints until you log out

---

## POST Todo (User ID)

### Updated Endpoint

```python
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency,
                      user: user_dependency,
                      todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    todo_model = Todos(**todo_request.model_dump())
    todo_model.owner_id = user.get("id")
    # todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("id"))

    db.add(todo_model)
    db.commit()
```

### Key Detail: Setting `owner_id`

The `TodoRequest` body doesn't include `owner_id` - it's taken from the authenticated user's JWT:

```python
todo_model.owner_id = user.get("id")
```

| Field | Source |
|-------|--------|
| `title`, `description`, `priority`, `complete` | Request body (`TodoRequest`) |
| `id` | Auto-incremented by the database |
| `owner_id` | Extracted from the JWT via `get_current_user` |

### Without a JWT → 401

If you try to create a to-do without authorizing first, you get `401 Authentication failed`.

---

## Get All Todos (User ID)

### Updated Endpoint

```python
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()
```

### What Changed

| Before | After |
|--------|-------|
| `db.query(Todos).all()` - returns every to-do | `.filter(Todos.owner_id == user.get("id")).all()` - only the user's to-dos |

A user now only sees their own to-dos, not anyone else's.

---

## Get Todo by ID (User ID)

### Updated Endpoint

```python
@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency,
                    user: user_dependency,
                    todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    todo_model = db.query(Todos)\
        .filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id"))\
        .first()

    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")
```

### Two Filters

| Filter | Purpose |
|--------|---------|
| `Todos.id == todo_id` | Match the requested to-do ID |
| `Todos.owner_id == user.get("id")` | Ensure it belongs to the authenticated user |

This prevents a user from fetching another user's to-do by guessing its ID. If either filter fails, the result is `None` and a `404` is returned.

### Behavior

| Input | Result |
|-------|--------|
| Valid ID owned by the user | Returns the to-do |
| Valid ID owned by someone else | `404 Todo not found` |
| Non-existent ID | `404 Todo not found` |
| No JWT | `401 Authentication failed` |

---

## PUT Todo (User ID)

### Updated Endpoint

```python
@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency,
                      user: user_dependency,
                      todo_request: TodoRequest,
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    todo_model = db.query(Todos)\
        .filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id"))\
        .first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()
```

### Same Dual-Filter Pattern

The query uses both `Todos.id == todo_id` and `Todos.owner_id == user.get("id")` so a user can only update their own to-dos.

| Scenario | Result |
|----------|--------|
| Own to-do, valid body | `204` - updated |
| Someone else's to-do | `404 Todo not found` |
| No JWT | `401 Authentication failed` |

### What the Client Sends

The request body includes `title`, `description`, `priority`, and `complete` - but **not** `id` or `owner_id`. The `owner_id` is already set on the record and never changes during an update.

---

## DELETE Todo (User ID)

### Updated Endpoint

```python
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency,
                      user: user_dependency,
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    todo_model = db.query(Todos)\
        .filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id"))\
        .first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.query(Todos)\
        .filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id"))\
        .delete()
    db.commit()
```

### Dual-Filter on Both Lookup and Delete

| Step | Filter Used | Why |
|------|-------------|-----|
| 1. Look up the to-do | `id + owner_id` | Confirm it exists and belongs to the user |
| 2. Delete | `id + owner_id` | Delete only the matching record |

A user can only delete their own to-dos. Attempting to delete someone else's returns `404`.

---

## Admin Router - Adding Role to JWT

### Why Add Role to the JWT?

The admin endpoints need to check whether the authenticated user has the `admin` role. Currently the JWT only carries `username` and `id`. We need to add `role`.

### Step 1 - Update `create_access_token`

```python
# routers/auth.py
def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "role": role}
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Step 2 - Pass Role When Creating the Token

```python
token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
```

### Step 3 - Decode Role in `get_current_user`

```python
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        return {"username": username, "id": user_id, "role": user_role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
```

### What the JWT Payload Now Contains

| Claim | Value |
|-------|-------|
| `sub` | username |
| `id` | user ID |
| `role` | `"admin"` or other role |
| `exp` | expiration time |

### Create the Admin Router File

```
routers/
├── auth.py
├── todos.py
└── admin.py      ← new
```

```python
# routers/admin.py
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])
```

### Include It in `main.py`

```python
from routers import auth, todos, admin

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
```

---

## Admin Endpoints

### Admin GET - View All Todos

```python
@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication failed")

    return db.query(Todos).all()
```

### The Admin Check

```python
if user is None or user.get("role") != "admin":
    raise HTTPException(status_code=401, detail="Authentication failed")
```

| Condition | Result |
|-----------|--------|
| Not logged in | `401 Authentication failed` |
| Logged in but not admin | `401 Authentication failed` |
| Logged in as admin | Returns all to-dos from all users |

### Admin DELETE - Delete Any Todo

```python
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,
                      db: db_dependency,
                      todo_id: int = Path(gt=0)):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication failed")

    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
```

### Key Difference from User Endpoints

| User Endpoint | Admin Endpoint |
|---------------|----------------|
| Filters by `owner_id == user.get("id")` | No `owner_id` filter - accesses all records |
| Only own to-dos | Any to-do in the database |
| Checks `user is None` | Checks `user is None` **and** `user.get("role") != "admin"` |

### Testing Admin Endpoints

1. **Log in as admin** (`admin` / `test1234`) → admin GET returns all to-dos
2. **Log in as regular user** (`tagore` / `test1234`) → admin GET returns `401`
3. **Admin DELETE** any to-do by ID → `204`, even if it belongs to another user
