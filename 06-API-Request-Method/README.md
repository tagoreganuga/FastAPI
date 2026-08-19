# API Request Method

## Table of Contents

- [Project Recap](#project-recap)
- [Database Dependency Injection](#database-dependency-injection)
- [GET - Fetch All To-Dos](#get---fetch-all-to-dos)
- [GET - Fetch To-Do by ID](#get---fetch-to-do-by-id)
- [Pydantic TodoRequest Model](#pydantic-todorequest-model)
- [POST - Create a To-Do](#post---create-a-to-do)
- [PUT - Update a To-Do](#put---update-a-to-do)
- [DELETE - Remove a To-Do](#delete---remove-a-to-do)

---

## Project Recap

The database and `todos` table already exist from the previous section. Now we connect that table to our FastAPI app and build all four CRUD endpoints (GET, POST, PUT, DELETE) against the real database.

### What Carries Over

- Pydantic request models with `Field` validation
- `HTTPException` for 404s
- `Path()` validation on path parameters
- Explicit `status_code` responses from `starlette`

### What's New

- **Dependency injection** - a reusable database session for every endpoint
- **SQLAlchemy queries** (`.query`, `.filter`, `.first()`, `.all()`, `.delete()`)
- A shared `db_dependency` shortcut so we don't repeat boilerplate on every endpoint

---

## Database Dependency Injection

### The `get_db` Function

Every endpoint needs a database session opened before it runs and closed after it returns. We do this with a dependency that uses `yield`.

```python
# main.py
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### How `yield` Works Here

| Step | What Happens |
|------|-------------|
| 1. Code before `yield` | Opens the session - runs **before** the endpoint |
| 2. `yield db` | Hands the session to the endpoint, which returns its response |
| 3. Code after `yield` (`finally`) | Closes the session - runs **after** the response is sent |

This makes the app faster and safer: the database connection is only held open for the duration of the request.

### What is Dependency Injection?

"Run something first, then inject the result into the function." Here, we open a DB session first, then inject it as the `db` parameter into the endpoint.

FastAPI's `Depends()` is what triggers this. We pair it with a type annotation so the endpoint knows `db` is a SQLAlchemy `Session`.

### The `db_dependency` Shortcut

Writing the full annotation every time is repetitive. Define it once at the top of the file and reuse it everywhere.

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

db_dependency = Annotated[Session, Depends(get_db)]
```

Now every endpoint just uses `db: db_dependency` instead of the long form.

---

## GET - Fetch All To-Dos

```python
from fastapi import FastAPI, status
from models import Todos

@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Todos).all()
```

### Testing

Visit `/docs`, open **GET /** → **Try it out** → **Execute**. You'll get all records in the database, each with its `id`, `title`, `description`, `priority`, and `complete`.

---

## GET - Fetch To-Do by ID

```python
from fastapi import FastAPI, Path, HTTPException, status

@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")
```

### Behavior

- `todo_id = 2` → returns the matching to-do
- `todo_id = 999` → `404 Todo not found`
- `todo_id = -1` → `422 Unprocessable Entity` (fails `Path(gt=0)` before the query runs)

> **Tip:** Path-parameter validation is checked before the endpoint body runs, so invalid IDs never hit the database.

---

## Pydantic TodoRequest Model

The body of POST and PUT requests needs validation. We create a Pydantic model that mirrors the `todos` table - **except the `id`**, because the database auto-increments it and the client never supplies it.

```python
from pydantic import BaseModel, Field

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool
```

### Why No `id` in the Request?

- `id` is the **primary key** - the database auto-increments it
- The client creating a to-do doesn't know what ID it will get
- SQLAlchemy assigns the correct ID automatically on commit

If validation fails on any field, FastAPI returns `422 Unprocessable Entity` automatically - no manual exception needed.

---

## POST - Create a To-Do

```python
@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo_model = Todos(**todo_request.model_dump())

    db.add(todo_model)
    db.commit()
```

### Breakdown

| Piece | Purpose |
|-------|---------|
| `@app.post("/todo")` | POST endpoint at `/todo` |
| `status_code=201` | Resource created successfully |
| `TodoRequest` as the body | Incoming JSON is validated against the Pydantic model |
| `**todo_request.model_dump()` | Unpack the validated dict into the `Todos` constructor |
| `db.add(...)` | Stage the new record in the session |
| `db.commit()` | Flush it to the database - the transaction actually happens here |

### `add` vs `commit`

| Action | What It Does |
|--------|-------------|
| `db.add(todo_model)` | Tells the session "we're about to add this" - nothing written yet |
| `db.commit()` | Writes the staged changes to the database permanently |

### Testing

1. **GET /** to see current to-dos
2. **POST /todo** → Try it out → fill in a title, description, priority, complete → Execute
3. You get a `201 Created` with a `null` body (nothing returned by design)
4. **GET /** again - the new to-do appears with an auto-incremented `id`

---

## PUT - Update a To-Do

```python
@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency,
                      todo_request: TodoRequest,
                      todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()
```

### Why We Modify the Existing Model

We fetch the record from the database and update **its** fields - we don't build a new `Todos` object. SQLAlchemy tracks the object it returned from the query, so when we commit, it issues an `UPDATE` for that row.

If we created a brand-new `Todos` object instead, SQLAlchemy would either:
- Try to insert a duplicate ID (error), or
- Insert a new row with a different auto-incremented ID (unwanted duplicate)

### Parameter Order Matters

Non-path parameters (like `todo_request`) must come **before** path-validated parameters (like `todo_id: int = Path(gt=0)`). Otherwise FastAPI raises a definition error.

### Testing

1. **GET /** and copy a to-do's body
2. **PUT /todo/{id}** → paste the body, change `priority` or `complete` → Execute
3. `204` means success with no response body
4. **GET /** again to confirm the fields changed

---

## DELETE - Remove a To-Do

```python
@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
```

### Testing

1. **POST** a dummy to-do, note its `id` (e.g., 5)
2. **GET /** to confirm it exists
3. **DELETE /todo/5** → Execute → `204`
4. **GET /** again - the to-do with `id=5` is gone
