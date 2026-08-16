# Move Fast With FastAPI

## Table of Contents

- [Books Project Overview](#books-project-overview)
- [Pydantic v1 vs Pydantic v2](#pydantic-v1-vs-pydantic-v2)
- [Project Setup](#project-setup)
- [POST Request Before Validation](#post-request-before-validation)
- [Pydantic & Data Validation Overview](#pydantic--data-validation-overview)
- [Pydantic Book Request Validation](#pydantic-book-request-validation)
- [Fields - Data Validation](#fields---data-validation)
- [Pydantic Configurations](#pydantic-configurations)
- [Fetch Book by ID](#fetch-book-by-id)
- [Fetch Books by Rating](#fetch-books-by-rating)
- [Update Book with PUT Request](#update-book-with-put-request)
- [Delete Book with DELETE Request](#delete-book-with-delete-request)
- [Data Validation - Path Parameters](#data-validation---path-parameters)
- [Data Validation - Query Parameters](#data-validation---query-parameters)
- [Status Codes Overview](#status-codes-overview)
- [HTTP Exceptions](#http-exceptions)
- [Explicit Status Code Responses](#explicit-status-code-responses)

---

## Books Project Overview

This project continues working with book API endpoints but makes them more sophisticated.

### What's Continued
- GET, POST, PUT, and DELETE request methods (CRUD operations)

### What's New
- Data validation
- Exception handling
- Status codes
- Swagger configuration
- Python request objects

### The Book Class

Books are now real Python objects instead of dictionaries.

```python
class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int

def __init__(self, id, title, author, description, rating):
    self.id = id
    self.title = title
    self.author = author
    self.description = description
    self.rating = rating
```

The `__init__` constructor initializes a Book object with values for id, title, author, description, and rating, and stores those values as instance attributes.

---

## Pydantic v1 vs Pydantic v2

FastAPI is compatible with both Pydantic v1 and v2. Based on your version, some method names change.

### The Three Biggest Changes

| Pydantic v1 | Pydantic v2 |
|-------------|------------|
| `.dict()` | `.model_dump()` |
| `schema_extra` inside a `Config` class | `json_schema_extra` |
| `Optional[int]` (no default needed) | `Optional[int] = None` (default required) |

> **Tip:** If `.dict()` throws a deprecation error, you're on Pydantic v2 - switch to `.model_dump()`.

---

## Project Setup

### Step 1 - Create the File and Import FastAPI

```python
# books2.py

from fastapi import FastAPI

app = FastAPI()
```

### Step 2 - Create the Book Class

```python
class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int

    def __init__(self, id, title, author, description, rating):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
```

### Step 3 - Populate the Books List

```python
BOOKS = [
    Book(1, "AWS", "Author 1", "AWS book", 5),
    Book(2, "Linux", "Author 2", "Linux book", 5),
    Book(3, "DevOps", "Author 3", "DevOps book", 4),
    Book(4, "Kubernetes", "Author 4", "Kubernetes book", 3),
    Book(5, "Docker", "Author 5", "Docker book", 4),
    Book(6, "Python", "Author 6", "Python book", 4),
]
```

### Step 4 - Create the First Endpoint

```python
@app.get("/books")
async def read_all_books():
    return BOOKS
```

### Step 5 - Run the Server

```bash
uvicorn books2:app --reload
```

Visit `/docs` to see the Swagger UI and test the endpoint.

---

## POST Request Before Validation

Create a POST endpoint to add new books.

```python
from fastapi import Body

@app.post("/create-book")
async def create_book(book_request=Body()):
    BOOKS.append(book_request)
```

### The Problem

Using `Body()` accepts any data - there's **no validation**. A user could submit:

- `id = -90`
- `rating = 1999`

Both would be accepted with a `200 OK` status. We need validation to enforce rules like rating between 1–5 and positive IDs.

---

## Pydantic & Data Validation Overview

### What is Pydantic?

Pydantic is a Python library for **data modeling, data parsing, and efficient error handling**. It's the standard way FastAPI validates incoming data.

### The Plan

1. Create a **`BookRequest`** model that inherits from Pydantic's `BaseModel`
2. Add **field validation** to each variable in the request
3. **Convert** the validated `BookRequest` into a `Book` object before saving

### BookRequest Model

```python
from pydantic import BaseModel, Field

class BookRequest(BaseModel):
    id: Optional[int] = None
    title: str = Field(...)
    author: str = Field(...)
    description: str = Field(...)
    rating: int = Field(...)
```

### Book Conversion Pattern

```python
@app.post("/create-book")
async def create_book(book_request: BookRequest):
    new_book = Book(**book_request.model_dump())
    BOOKS.append(new_book)
```

#### The `**` (Double Asterisk) Operator

`book_request.model_dump()` returns a dictionary. The `**` unpacks that dictionary into keyword arguments for the `Book` constructor - matching each key to the corresponding parameter.

---

## Pydantic Book Request Validation

### Step 1 - Import BaseModel

```python
from pydantic import BaseModel
```

### Step 2 - Create BookRequest

```python
class BookRequest(BaseModel):
    id: int
    title: str
    author: str
    description: str
    rating: int
```

### Step 3 - Use BookRequest as the Parameter Type

```python
@app.post("/create-book")
async def create_book(book_request: BookRequest):
    new_book = Book(**book_request.model_dump())
    BOOKS.append(new_book)
```

### Why Convert BookRequest to Book?

Without conversion, the list would contain a mix of `BookRequest` objects and `Book` objects. Converting keeps `Book` as the single source of truth.

### Pydantic v1 vs v2 Dictionary Method

```python
# Pydantic v1
new_book = Book(**book_request.dict())

# Pydantic v2
new_book = Book(**book_request.model_dump())
```

---

## Fields - Data Validation

Import `Field` to add validation rules to each field.

```python
from pydantic import BaseModel, Field
```

### String Validation

```python
class BookRequest(BaseModel):
    id: Optional[int] = None
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)   # rating must be between 1 and 5
```
If validation fails, FastAPI automatically returns a `422 Unprocessable Entity` error with a helpful message.

### Auto-Incrementing the Book ID

The client shouldn't supply the ID - the server should assign it.

```python
def find_book_id(book: Book):
    if len(BOOKS) > 0:
        book.id = BOOKS[-1].id + 1
    else:
        book.id = 1
    return book
```

#### Ternary Operator Version

```python
book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
```

#### Usage in the POST Endpoint

```python
@app.post("/create-book")
async def create_book(book_request: BookRequest):
    new_book = Book(**book_request.model_dump())
    find_book_id(new_book)
    BOOKS.append(new_book)
```

### Making the ID Optional

Since the client doesn't know the ID when creating a book, make it optional:

```python
from typing import Optional

class BookRequest(BaseModel):
    id: Optional[int] = None    # must include = None for Pydantic v2
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)
```

---

## Pydantic Configurations

### Adding a Description to a Field

```python
id: Optional[int] = Field(default=None, description="ID is not needed on create")
```

This description appears in the Swagger schema.

### Setting Example Values with `model_config`

Pre-populate the Swagger UI with example values:

```python
class BookRequest(BaseModel):
    id: Optional[int] = Field(default=None, description="ID is not needed on create")
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new book",
                "author": "Author name",
                "description": "A new description of a book",
                "rating": 5
            }
        }
    }
```

### Pydantic v1 vs v2 Configuration

| Pydantic v1 | Pydantic v2 |
|-------------|------------|
| `class Config: schema_extra = {...}` | `model_config = {"json_schema_extra": {...}}` |

---

## Fetch Book by ID

Create a GET endpoint with a **path parameter**.

```python
@app.get("/books/{book_id}")
async def read_book(book_id: int):
    for book in BOOKS:
        if book.id == book_id:
            return book
```

### Path Parameter vs Query Parameter

| Type | URL Example | How It's Passed |
|------|-------------|-----------------|
| Path parameter | `/books/3` | Part of the URL path |
| Query parameter | `/books/?book_rating=5` | After `?` in the URL |

---

## Fetch Books by Rating

Create a GET endpoint with a **query parameter** to filter books.

```python
@app.get("/books/")
async def read_book_by_rating(book_rating: int):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)
    return books_to_return
```

### How It Works

- Calling `/books/?book_rating=5` returns all books with a rating of 5
- This is a **query parameter**, so it doesn't interfere with the path parameter endpoint `/books/{book_id}`
- Order matters from top to bottom in your file - similar paths must be ordered carefully

---

## Update Book with PUT Request

A PUT request updates an existing object.

```python
@app.put("/books/update_book")
async def update_book(book: BookRequest):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:
            BOOKS[i] = book
```

### How It Works

1. The client sends a full book object (including the `id`) in the request body
2. The server loops through the books list
3. When a matching ID is found, that book is replaced with the new data
4. The `id` field in `BookRequest` is optional - but for updates, the client **must** provide it

---

## Delete Book with DELETE Request

A DELETE request removes an object.

```python
@app.delete("/books/{book_id}")
async def delete_book(book_id: int):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            break
```

### How It Works

1. The client passes a `book_id` as a path parameter
2. The server loops through the books list
3. When a matching ID is found, that book is removed with `.pop(i)`
4. `break` exits the loop after deletion

---

## Data Validation - Path Parameters

Import `Path` to validate path parameters.

```python
from fastapi import FastAPI, Path

@app.get("/books/{book_id}")
async def read_book(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
```

### Applying to the Delete Endpoint Too

```python
@app.delete("/books/{book_id}")
async def delete_book(book_id: int = Path(gt=0)):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            break
```

### Result

- `book_id = 3` → works (returns the book)
- `book_id = 0` → `422 Unprocessable Entity` error: "ensure this value is greater than 0"

---

## Data Validation - Query Parameters

Import `Query` to validate query parameters.

```python
from fastapi import FastAPI, Path, Query

@app.get("/books/")
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)
    return books_to_return
```

### Validation Rules

| Parameter | Validation | Error if Violated |
|-----------|------------|-------------------|
| `book_rating` | `gt=0, lt=6` (1–5) | "ensure this value is less than 6" |
| `published_date` | `gt=1999, lt=2031` (2000–2030) | "ensure this value is greater than 1999" |

---

## Status Codes Overview

HTTP status codes tell the client what happened on the server side.

### Status Code Series

| Series | Meaning | Examples |
|--------|---------|----------|
| **1xx** | Informational Response: Request Processing. | |
| **2xx** | Success: Request Successful completion. | 200 OK, 201 Created, 204 No Content |
| **3xx** | Redirection: Further action is needed. | |
| **4xx** | Client Errors: An error caused by the client. | 400 Bad Request, 401 Unauthorized, 404 Not Found, 422 Unprocessable Entity |
| **5xx** | Server Errors: An error occurred on the server side. | 500 Internal Server Error |

### Common Status Codes

| Code | Name | When to Use |
|------|------|-------------|
| **200** | OK | Successful GET request that returns data |
| **201** | Created | Successful POST that creates a new resource |
| **204** | No Content | Successful PUT/DELETE that doesn't return data |
| **400** | Bad Request | Invalid request format |
| **401** | Unauthorized | Missing or invalid authentication |
| **404** | Not Found | Requested resource doesn't exist |
| **422** | Unprocessable Entity | Semantic validation error |
| **500** | Internal Server Error | Unexpected server-side failure |

---

## HTTP Exceptions

Import `HTTPException` to raise errors when something goes wrong.

```python
from fastapi import FastAPI, Path, Query, HTTPException
```

### Adding a 404 to the Fetch Book Endpoint

```python
@app.get("/books/{book_id}")
async def read_book(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Item not found")
```

### Adding a 404 to the Update (PUT) Endpoint

Use a boolean flag to track whether the update happened.

```python
@app.put("/books/update_book")
async def update_book(book: BookRequest):
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:
            BOOKS[i] = book
            book_changed = True
    if not book_changed:
        raise HTTPException(status_code=404, detail="Item not found")
```

### Adding a 404 to the Delete Endpoint

```python
@app.delete("/books/{book_id}")
async def delete_book(book_id: int = Path(gt=0)):
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_changed = True
            break
    if not book_changed:
        raise HTTPException(status_code=404, detail="Item not found")
```

### The Boolean Flag Pattern

| Step | What Happens |
|------|-------------|
| 1. Set `book_changed = False` | Assume nothing will happen |
| 2. If the book is found and updated/deleted, set `book_changed = True` | Confirm the operation succeeded |
| 3. After the loop, if `book_changed` is still `False`, raise `HTTPException` | The book wasn't found |

---

## Explicit Status Code Responses

Import `status` from Starlette (installed automatically with FastAPI).

```python
from starlette import status
```

### Adding Status Codes to Each Endpoint

```python
# GET - returns data → 200 OK
@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_books():
    return books

# GET by ID - returns data → 200 OK
@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book(book_id: int = Path(gt=0)):
    ...

# GET by rating - returns data → 200 OK
@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    ...

# POST - creates a resource → 201 Created
@app.post("/create-book", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
    ...

# PUT - updates but returns nothing → 204 No Content
@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    ...

# DELETE - deletes but returns nothing → 204 No Content
@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Path(gt=0)):
    ...
```

### How HTTP Exceptions Override Status Codes

Even though an endpoint is set to return `200 OK`, if a book isn't found the `raise HTTPException(status_code=404)` will override it and return `404 Not Found` instead.