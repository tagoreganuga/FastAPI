from typing import Optional
from fastapi import FastAPI, Path, Query, HTTPException, Body
from pydantic import BaseModel, Field
from starlette import status

# Initialize the FastAPI application
app = FastAPI()

# ==========================================
# DATA MODELS
# ==========================================

class Book:
    """
    Standard Python class representing a Book in our "database".
    """
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id, title, author, description, rating, published_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    """
    Pydantic BaseModel for Data Validation and Type Checking on incoming requests.
    Validates data when creating or updating a book.
    """
    # ID is optional on creation, it will be assigned automatically
    id: Optional[int] = Field(description='ID is not needed on create', default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    # Rating must be between 1 and 5 (greater than 0, less than 6)
    rating: int = Field(gt=0, lt=6)
    # Published date must be between 2000 and 2030
    published_date: int = Field(gt=1999, lt=2031)

    # Configuration to provide an example schema in the OpenAPI / Swagger docs
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new book",
                "author": "codingwithroby",
                "description": "A new description of a book",
                "rating": 5,
                'published_date': 2029
            }
        }
    }


# ==========================================
# MOCK DATABASE
# ==========================================

# In-memory list acting as our database
BOOKS = [
    Book(1, "AWS", "Author 1", "AWS book", 5, 2021),
    Book(2, "Linux", "Author 2", "Linux book", 5, 2022),
    Book(3, "DevOps", "Author 3", "DevOps book", 4, 2023),
    Book(4, "Kubernetes", "Author 4", "Kubernetes book", 3, 2024),
    Book(5, "Docker", "Author 5", "Docker book", 4, 2025),
    Book(6, "Python", "Author 6", "Python book", 4, 2026),
]


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_books():
    """Retrieve all books from the database."""
    return BOOKS


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book(book_id: int = Path(gt=0)):
    """
    Retrieve a single book by its ID.
    Validates that the path parameter (book_id) is greater than 0.
    """
    for book in BOOKS:
        if book.id == book_id:
            return book
    # If book isn't found, return a 404 error
    raise HTTPException(status_code=404, detail='Item not found')


@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    """
    Filter books by rating using a query parameter (e.g., /books/?book_rating=5).
    Validates that the query parameter is between 1 and 5.
    """
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)
    return books_to_return


@app.get("/books/publish/", status_code=status.HTTP_200_OK)
async def read_books_by_publish_date(published_date: int = Query(gt=1999, lt=2031)):
    """
    Filter books by their published date using a query parameter.
    Validates that the query parameter is between 2000 and 2030.
    """
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            books_to_return.append(book)
    return books_to_return


@app.post("/create-book", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
    """
    Create a new book. Uses BookRequest for validation.
    The response status is set to 201 Created.
    """
    # Convert the validated Pydantic model into our standard Python Book class
    new_book = Book(**book_request.model_dump())
    # Append the new book after assigning it a new auto-incremented ID
    BOOKS.append(find_book_id(new_book))


def find_book_id(book: Book):
    """Helper function to auto-generate the next sequential ID for a new book."""
    book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
    return book


@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    """
    Update an existing book. Uses BookRequest to validate incoming data.
    Returns 204 No Content on successful update.
    """
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:
            # Overwrite the old book data with the new validated request data
            # Note: We create a new Book instance here to ensure it aligns with our mock DB type
            BOOKS[i] = Book(**book.model_dump())
            book_changed = True
            break # Added break for efficiency
            
    # If the ID provided doesn't match any existing book, return 404
    if not book_changed:
        raise HTTPException(status_code=404, detail='Item not found')


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Path(gt=0)):
    """
    Delete a book by its ID.
    Validates that the path parameter is greater than 0.
    Returns 204 No Content on successful deletion.
    """
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_changed = True
            break
            
    # If the ID provided doesn't match any existing book, return 404
    if not book_changed:
        raise HTTPException(status_code=404, detail='Item not found')