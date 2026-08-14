# FastAPI Request Method Logic

## Table of Contents

- [Books Project Introduction](#books-project-introduction)
- [GET Request Method Overview](#get-request-method-overview)
- [Path Parameters](#path-parameters)
- [Query Parameters](#query-parameters)
- [POST Request Method](#post-request-method)
- [PUT Request Method](#put-request-method)
- [DELETE Request Method](#delete-request-method)

---

## Books Project Introduction

First project using FastAPI - a books API to learn all basic HTTP request methods.

Each book is a dictionary with key-value pairs: **title**, **author**, **category**.

```python
BOOKS = [
    {"title": "Title 1", "author": "Author 1", "category": "science"},
    {"title": "Title 2", "author": "Author 2", "category": "science"},
    {"title": "Title 3", "author": "Author 3", "category": "history"},
    {"title": "Title 4", "author": "Author 4", "category": "math"},
    {"title": "Title 5", "author": "Author 5", "category": "math"},
    {"title": "Title 6", "author": "Author 2", "category": "math"},
]
```

> Author 2 wrote two books: Title 2 (science) and Title 6 (math).

### CRUD Operations & HTTP Methods

| CRUD | HTTP Method | Purpose |
| --- | --- | --- |
| **C**reate | `POST` | Create new data |
| **R**ead | `GET` | Read/return data |
| **U**pdate | `PUT` | Update existing data |
| **D**elete | `DELETE` | Remove data |

### Request & Response Flow

```text
Web Page  →  Request (HTTP method)  →  FastAPI Server  →  Response (data)  →  Web Page
```

The web page sends a request using HTTP methods. FastAPI processes it and sends a response back.

### Swagger UI

FastAPI includes **Swagger UI** automatically - no setup needed.

- Visit: `http://127.0.0.1:8000/docs`
- Lists all API endpoints
- Call each endpoint and see responses
- Shows status codes (200 = success)

---

## GET Request Method Overview

**Purpose:** Read and return data to the client.

### Basic App Setup

```python
# books.py

# This will allow us to use all of the dependencies that we installed to our env
from fastapi import FastAPI

# This allows us to use those dependencies that came with FastAPI in a Variable within our application
app = FastAPI()

# This defines the endpoint and the function that runs when the endpoint is called
@app.get("/api-endpoint")
async def first_api():
    return {"message": "Hello Tagore!"}
```

| Part | What It Does |
| --- | --- |
| `from fastapi import FastAPI` | Imports the framework |
| `app = FastAPI()` | Creates the application instance |
| `@app.get("/api-endpoint")` | Decorator - defines HTTP method and URL path |
| `async def` | The function that runs when the endpoint is called |
| `async` | Optional - FastAPI handles async behind the scenes |

### Starting the Application

```bash
# Using uvicorn (with auto-reload on code changes)
uvicorn books:app --reload

# Alternative: FastAPI CLI
fastapi dev books.py      # development mode
fastapi run books.py      # production mode
```

- `books` = the Python file name (books.py)
- `app` = the variable inside that file (`app = FastAPI()`)
- `--reload` = restart server automatically when code changes

App runs at: `http://127.0.0.1:8000`

> Stop the server with `Ctrl+C`.

### Enhance GET Request

Return a list of books instead of a simple message.

```python
@app.get("/books")
async def read_all_books():
    return BOOKS
```

- Visiting `http://127.0.0.1:8000/books` returns all books
- Changed path from `/api_endpoint` to `/books` so the URL tells the client what to expect
- Changed function name from `first_api` to `read_all_books` for clarity

---

## Path Parameters

**What:** Dynamic values attached to the URL path - used to find information based on location (like a file system).

```text
http://127.0.0.1:8000/books/Title%201
                            ↑↑↑↑↑↑↑↑↑↑
                         dynamic path parameter
```

### How It Works

```python
@app.get("/books/{book_title}")
async def read_book(book_title: str):
    for book in BOOKS:
        if book["title"].casefold() == book_title.casefold():
            return book
```

| Step | Detail |
| --- | --- |
| `{book_title}` in the path | Captures whatever the user types after `/books/` |
| `book_title` parameter | Must match the name in curly brackets |
| `: str` | Explicit type - FastAPI converts input to string |
| `.casefold()` | Stronger version of `.lower()` - for case-insensitive matching |

### Order Matters!

FastAPI checks routes **top to bottom**. Put static paths before dynamic ones:

```python
# CORRECT - static first
@app.get("/books/mybook")
async def read_my_book():
    return {"book_title": "My Favorite Book"}

# Then dynamic - catches everything else
@app.get("/books/{book_title}")
async def read_book(book_title: str):
    ...
```

If the dynamic route comes first, `/books/mybook` gets caught by it and the static route never runs.

### URL Encoding

URLs can't have spaces - use `%20`:

| URL | Meaning |
| --- | --- |
| `/books/Title%201` | `Title 1` |
| `/books/Author%204` | `Author 4` |

---

## Query Parameters

**What:** Filter data using name-value pairs after a `?` in the URL.

```text
http://127.0.0.1:8000/books/?category=science
                           ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                       query parameter (name=value)
```

### How It Works

```python
@app.get("/books/")
async def read_category_by_query(category: str):
    books_to_return = []
    for book in BOOKS:
        if book["category"].casefold() == category.casefold():
            books_to_return.append(book)
    return books_to_return
```

- FastAPI automatically knows `category` is a query parameter (not in the path)
- The parameter name must match the query name in the URL

### Combining Path + Query Parameters

```python
@app.get("/books/{book_author}/")
async def read_author_category_by_query(book_author: str, category: str):
    books_to_return = []
    for book in BOOKS:
        if (book["author"].casefold() == book_author.casefold() \
                and book["category"].casefold() == category.casefold()):
            books_to_return.append(book)
    return books_to_return
```

URL: `http://127.0.0.1:8000/books/Author%202/?category=science`

| Parameter | Source | Value |
| --- | --- | --- |
| `book_author` | Path parameter | `Author 2` |
| `category` | Query parameter | `science` |

> **Rule of thumb:** Use path parameters to find a location, query parameters to filter results.

---

## POST Request Method

**Purpose:** Create new data. Can include a **body** (GET requests does not have).

```python
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/books/create_book")
async def create_book(new_book=Body()):
    BOOKS.append(new_book)
```

| Part | Detail |
| --- | --- |
| `@app.post` | Defines a POST endpoint |
| `Body()` | Extracts data from the request body |
| `new_book` | The incoming book dictionary |

### Request Body Example

```json
{
    "title": "Title 7",
    "author": "Author 2",
    "category": "math"
}
```

> Use **double quotes** in the body - single quotes will cause errors.

### Key Points

- GET requests **cannot** have a body (even if you add `Body()`, it will error at runtime)
- POST requests **can** have a body
- After creating, verify by calling the GET `/books` endpoint

---

## PUT Request Method

**Purpose:** Update existing data. Like POST, it can include a body.

```python
@app.put("/books/update_book")
async def update_book(updated_book=Body()):
    for i in range(len(BOOKS)):
        if BOOKS[i]["title"].casefold() == updated_book["title"].casefold():
            BOOKS[i] = updated_book
```

| Step | Detail |
| --- | --- |
| Loop through books | `for i in range(len(BOOKS))` |
| Match by title | Compare titles using `.casefold()` |
| Replace at index | `BOOKS[i] = updated_book` |

### Example

Send this body to update Title 6's category from math to history:

```json
{
    "title": "Title 6",
    "author": "Author 2",
    "category": "history"
}
```

> The title is used to find the book. The author and category get updated.

---

## DELETE Request Method

**Purpose:** Remove data. Uses a path parameter to identify what to delete.

```python
@app.delete("/books/delete_book/{book_title}")
async def delete_book(book_title: str):
    for i in range(len(BOOKS)):
        if BOOKS[i]["title"].casefold() == book_title.casefold():
            BOOKS.pop(i)
            break
```

| Step | Detail |
| --- | --- |
| Path parameter | `book_title` identifies which book to delete |
| Loop through books | Find the matching title |
| Remove with `.pop(i)` | Deletes the book at that index |
| `break` | Stop looping after deletion |

### Example

URL: `http://127.0.0.1:8000/books/delete_book/Title%204`

This removes Title 4 from the list.
