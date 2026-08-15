from fastapi import Body, FastAPI

# Initialize the FastAPI application instance
app = FastAPI()

# In-memory database of books represented as a list of dictionaries
BOOKS = [
    {"title": "Title 1", "author": "Author 1", "category": "science"},
    {"title": "Title 2", "author": "Author 2", "category": "science"},
    {"title": "Title 3", "author": "Author 3", "category": "history"},
    {"title": "Title 4", "author": "Author 4", "category": "math"},
    {"title": "Title 5", "author": "Author 5", "category": "math"},
    {"title": "Title 6", "author": "Author 2", "category": "math"},
]


# ==========================================
# GET ENDPOINTS (Read Operations)
# ==========================================

@app.get("/books")
async def read_all_books():
    """Retrieve the complete list of all books."""
    return BOOKS


@app.get("/books/{book_title}")
async def read_book(book_title: str):
    """Retrieve a single book by its title using a path parameter."""
    for book in BOOKS:
        # Case-insensitive comparison of the title
        if book.get("title").casefold() == book_title.casefold():
            return book


@app.get("/books/")
async def read_category_by_query(category: str):
    """Filter and retrieve books by category using a query parameter (e.g., /books/?category=math)."""
    books_to_return = []
    for book in BOOKS:
        # Case-insensitive check for category match
        if book.get("category").casefold() == category.casefold():
            books_to_return.append(book)
    return books_to_return


@app.get("/books/byauthor/")
async def read_books_by_author_path(author: str):
    """Filter and retrieve books by author using a query parameter (e.g., /books/byauthor/?author=Author 2)."""
    books_to_return = []
    for book in BOOKS:
        # Case-insensitive check for author match
        if book.get("author").casefold() == author.casefold():
            books_to_return.append(book)
    return books_to_return


@app.get("/books/{book_author}/")
async def read_author_category_by_query(book_author: str, category: str):
    """
    Filter books by both author (path parameter) and category (query parameter).
    Example: /books/Author%202/?category=math
    """
    books_to_return = []
    for book in BOOKS:
        # Check if both author and category match (case-insensitive)
        if (
            book.get("author").casefold() == book_author.casefold()
            and book.get("category").casefold() == category.casefold()
        ):
            books_to_return.append(book)
    return books_to_return


# ==========================================
# POST ENDPOINTS (Create Operations)
# ==========================================

@app.post("/books/create_book")
async def create_book(new_book=Body()):
    """Add a new book to the database from the JSON request body."""
    BOOKS.append(new_book)


# ==========================================
# PUT ENDPOINTS (Update Operations)
# ==========================================

@app.put("/books/update_book")
async def update_book(updated_book=Body()):
    """Find an existing book by its title and update its contents with the request body."""
    for i in range(len(BOOKS)):
        # Match title to find the index of the book to update
        if BOOKS[i].get("title").casefold() == updated_book.get("title").casefold():
            BOOKS[i] = updated_book


# ==========================================
# DELETE ENDPOINTS (Delete Operations)
# ==========================================

@app.delete("/books/delete_book/{book_title}")
async def delete_book(book_title: str):
    """Find and remove a book by its title passed as a path parameter."""
    for i in range(len(BOOKS)):
        # Match title to find and remove the book from the list
        if BOOKS[i].get("title").casefold() == book_title.casefold():
            BOOKS.pop(i)
            break  # Exit loop once the target book is deleted