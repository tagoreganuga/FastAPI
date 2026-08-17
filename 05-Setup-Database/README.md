# Setup Database

## Table of Contents

- [To-Dos Project Overview](#to-dos-project-overview)
- [SQL Database Introduction](#sql-database-introduction)
- [Database Connection with ORM SQLAlchemy](#database-connection-with-orm-sqlalchemy)
- [Database Tables (Models)](#database-tables-models)
- [Main - Create Database Connection for API](#main---create-database-connection-for-api)
- [Installation of SQLite3 Terminal (Windows)](#installation-of-sqlite3-terminal-windows)
- [Installation of SQLite3 Terminal (Mac)](#installation-of-sqlite3-terminal-mac)
- [SQL Queries Introduction](#sql-queries-introduction)
- [SQLite3 Setting Up Todos](#sqlite3-setting-up-todos)

---

## To-Dos Project Overview

This project switches from books to **To-Dos** as the primary object and introduces several major new features.

### New Features

| Feature | Description |
|---------|-------------|
| **Full SQL Database** | All records and tables stored in a real database |
| **Three Database Options** | SQLite (embedded), PostgreSQL (production), MySQL (production) |
| **Authentication (JWT)** | Users log in with a username and password |
| **Authorization** | Role-based access - admins get endpoints regular users don't |
| **Password Hashing** | Passwords are hashed before saving - never stored as plain text |

### Architecture Overview

```
Web Page (Frontend)
      ↕  JWT / Authentication
FastAPI Server
      ↕  Retrieve users & to-dos
   Database
```

- The **web page** communicates with the **FastAPI server** using JWT tokens to determine who is authenticated
- The **FastAPI server** communicates with the **database** to retrieve users and to-dos, validating them against what the client sends

### What Continues from Previous Projects

- Creating table models (like the To-Do table model)
- CRUD operations (GET, POST, PUT, DELETE)
- Data validation with Pydantic
- Exception handling and status codes
- Swagger documentation

### Security Highlights

- **Password Hashing:** A hashing algorithm converts passwords into a hashed form before saving to the database. Even if the database is hacked, the original passwords remain protected.
- **JWT Authentication:** JSON Web Tokens are used to verify a user's identity on each request.
- **Role-Based Authorization:** Different users have different access levels - an admin can access endpoints that regular users cannot.

---

## SQL Database Introduction

### What is a Database?

A database is an **organized collection of structured information/data** stored in a computer system. The data can be:

- Easily accessed
- Modified
- Controlled and organized

Many databases use **SQL (Structured Query Language)** to modify and write data to database tables.

### What is Data?

Data can be related to just about any object. For example, a user on an application may have:

| Characteristic | Example |
|---------------|---------|
| Name | "Tagore" |
| Age | 23 |
| Email | "tagore@example.com" |
| Password | "password123" |

Each user has these four pieces of data associated with them. A database is simply a collection of this data, organized so it can be retrieved, stored, and modified.

### Database Management System (DBMS)

A **DBMS** is the application/software in charge of the database.

| Popular SQL Databases | Type |
|---------------------|------|
| **SQLite** | First DBMS used in this course |
| **MySQL** | Very popular choice |
| **PostgreSQL** | Another excellent choice |

### What is SQL?

SQL (pronounced "S-Q-L" or "sequel") is the **standard language for dealing with relational databases**. A relational database uses tables with columns and rows - like an Excel sheet.

### SQL CRUD Operations

SQL handles all CRUD operations within a database:

| CRUD Operation | SQL Command |
|---------------|-------------|
| **C**reate | `INSERT` |
| **R**ead | `SELECT` |
| **U**pdate | `UPDATE` |
| **D**elete | `DELETE` |

These map directly to HTTP request methods (POST, GET, PUT, DELETE).

---

## Database Connection with ORM SQLAlchemy

### Project Setup

1. Create a new Python package called `TodoApp`
2. Inside it, create a file called `database.py`

### What is SQLAlchemy?

**SQLAlchemy** is an ORM (Object-Relational Mapping) library. It lets us create databases, manage connections, and interact with database records using Python objects instead of raw SQL.

### Install SQLAlchemy

```bash
pip install sqlalchemy
```

### database.py - Full Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Database URL - location of the SQLite database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"

# 2. Create the engine - opens the connection to the database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 3. Create SessionLocal - each instance becomes a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create the Base - used to define database tables/models
Base = declarative_base()
```

### Breakdown of Each Component

#### Database URL
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"
```
- `sqlite:///` - tells SQLAlchemy to use SQLite
- `./todosapp.db` - the database file is created in the current directory

#### Engine
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
```
- The engine opens and manages the database connection
- `check_same_thread: False` - by default SQLite only allows one thread to communicate with it. FastAPI uses multiple threads, so we disable this check

#### SessionLocal
```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
- Each instance of `SessionLocal` becomes a database session
- `autocommit=False` - we control when changes are saved
- `autoflush=False` - we control when changes are flushed to the database
- `bind=engine` - the session uses the engine we created

#### Base
```python
Base = declarative_base()
```
- `Base` is the foundation class that all database models inherit from
- Used later to create database tables

### Database Connection Flow

```bash
database.py
     │
     ├── DATABASE URL
     │      ↓
     │   "todosapp.db"
     │
     ├── ENGINE
     │      ↓
     │   Communicates with DB
     │
     ├── SESSION
     │      ↓
     │   Performs DB operations
     │
     └── BASE
            ↓
       Defines Models
            ↓
       Todo / User / Book
```

---

## Database Tables (Models)

### What is a Model?

A model defines the **structure of a database table** - its columns and data types. Each model class becomes a table in the database.

### Create models.py

```python
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
```

---

## Main - Create Database Connection for API

### Create main.py

This file creates the FastAPI app and automatically generates the database and tables.

```python
from fastapi import FastAPI
from database import engine
import models

app = FastAPI()

# Create the database tables automatically
models.Base.metadata.create_all(bind=engine)
```

### How It Works

1. `from database import engine` - imports the engine from database.py
2. `import models` - imports the Todos model
3. `models.Base.metadata.create_all(bind=engine)` - SQLAlchemy reads all models that inherit from `Base` and creates their tables in the database

### Running the Application

```bash
cd TodoApp
uvicorn main:app --reload
```

When the server starts, SQLAlchemy automatically creates:
- A `todos.db` file in the `TodoApp` directory
- A `todos` table with all columns defined in the model

> **Note:** No SQL queries needed - SQLAlchemy handles everything behind the scenes.

---

## Installation of SQLite3 Terminal (Windows)

### Step-by-Step

1. Go to **https://www.sqlite.org/index.html**
2. Click **Download**
3. Scroll to **Precompiled Binaries for Windows**
4. Download **sqlite-tools-win32-x86** (the last option - includes command line tools)
5. Extract the downloaded ZIP file
6. Copy the extracted files to your **C: drive**
7. Rename the folder to **sqlite3**
8. Copy the full path (e.g., `C:\sqlite3`)

### Add to Environment Variables

1. Press **Windows key** → type **env** → open **Environment Variables**
2. Under **System variables** → find **Path** → click **Edit**
3. Click **New** → paste the SQLite3 path
4. Click **OK** on all three windows

### Verify Installation

Open Command Prompt and type:

```bash
sqlite3
```

If installed correctly, you'll see the SQLite version printed.

---

## Installation of SQLite3 Terminal (Mac)

### Step 1 - Install Homebrew

1. Go to **https://brew.sh**
2. Copy the installation command
3. Open Terminal → paste the command → press Enter
4. Enter your password when prompted
5. Press Return to continue

### Step 2 - Verify or Install SQLite3

```bash
# Check if SQLite is already installed via Homebrew
brew list

# If not installed, install it
brew install sqlite
```

### Step 3 - Verify Installation

```bash
sqlite3
```

You should see the SQLite version. To exit, type:

```sql
.quit
```

---

## SQL Queries Introduction

### The To-Do Record Structure

| Column | Description |
|--------|-------------|
| `id` | Primary key - unique identifier (auto-incremented) |
| `title` | Title of the to-do |
| `description` | Details about the to-do |
| `priority` | How important it is |
| `complete` | Whether it's done (true/false) |

### INSERT - Create Records

```sql
-- Insert a single to-do
INSERT INTO todos (title, description, priority, complete)
VALUES ('Go to store', 'Pick up eggs', 5, false);
```

> **Note:** We don't include `id` - the database auto-increments it so we never accidentally assign the same primary key to two records.

```sql
-- Insert another to-do
INSERT INTO todos (title, description, priority, complete)
VALUES ('Haircut', 'Need to get length of 1 millimeter', 3, false);
```

### SELECT - Read Records

```sql
-- Select ALL columns and ALL rows
SELECT * FROM todos;

-- Select only the title column
SELECT title FROM todos;

-- Select only the description column
SELECT description FROM todos;

-- Select multiple columns
SELECT title, description FROM todos;

-- Select three columns
SELECT title, description, priority FROM todos;
```

### WHERE - Filter Records

The `WHERE` clause specifies criteria that field values must meet.

```sql
-- Filter by priority
SELECT * FROM todos WHERE priority = 5;

-- Filter by title
SELECT * FROM todos WHERE title = 'Feed dog';

-- Filter by ID (most common - used when API passes an ID)
SELECT * FROM todos WHERE id = 2;
```

### UPDATE - Modify Records

```sql
-- Update by ID (best practice - ID is always unique)
UPDATE todos SET complete = true WHERE id = 5;

-- Update by title (risky - title may not be unique)
UPDATE todos SET complete = true WHERE title = 'Learn something new';
```

> **Warning:** Always update by primary key when possible. Updating by a non-unique field (like title) can modify multiple records unintentionally.

### DELETE - Remove Records

```sql
-- Delete by ID (best practice)
DELETE FROM todos WHERE id = 5;

-- Delete by a non-unique field (dangerous!)
DELETE FROM todos WHERE complete = false;
```

> **Warning:** `DELETE FROM todos WHERE complete = false` would delete ALL incomplete records - potentially wiping the entire table. Always use the primary key for single-record deletions.

### Soft Deletes

Many applications don't permanently delete records. Instead, they move "deleted" records to a separate table so users keep their history. The record is removed from the main table but preserved elsewhere.

---

## SQLite3 Setting Up Todos

### Opening the Database

```bash
# Navigate to your TodoApp folder
cd TodoApp

# Open the SQLite database
sqlite3 todos.db
```

### Useful SQLite3 Commands

| Command | Purpose |
|---------|---------|
| `.schema` | Show all tables and their structure |
| `.mode column` | Display results in column format |
| `.mode markdown` | Display results in markdown table format |
| `.mode box` | Display results in a boxed format |
| `.mode table` | Display results in a table with dashed lines |
| `.quit` | Exit SQLite3 |

> **Tip:** If you see `...>` after typing a command, you forgot a semicolon `;`. Type `;` and press Enter to complete the command.
