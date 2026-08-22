# Large Production Database Setup

## Table of Contents

- [Production DBMS Overview](#production-dbmss-overview)
- [PostgreSQL Introduction](#postgresql-introduction)
- [PostgreSQL Create Database & Tables](#postgresql-create-database--tables)
- [PostgreSQL Connect to FastAPI](#postgresql-connect-to-fastapi)
- [MySQL Introduction](#mysql-introduction)
- [MySQL Create Database & Tables](#mysql-create-database--tables)
- [MySQL Connect to FastAPI](#mysql-connect-to-fastapi)

---

## Production DBMSs Overview

When an application grows beyond small/medium size, it's time to move from SQLite to a **production database management system (DBMS)**. Where we'll cover two of the most popular options: **PostgreSQL** and **MySQL**.

### What We Cover

| Topic | Details |
|-------|---------|
| Install PostgreSQL | Windows and Mac |
| Install MySQL | Windows and Mac |
| Create database & tables | Matching our SQLite schema |
| Connect FastAPI | Swap the connection string |
| CRUD operations | All endpoints work the same after connecting |

### SQLite vs Production Databases

| Feature | SQLite | PostgreSQL / MySQL |
|---------|--------|---------------------|
| **Storage** | In-memory or local file on disk | Runs on its own server and port |
| **Setup** | Zero configuration, ships with the app | Separate install, server process, authentication |
| **Deployment** | Deploy alongside the application | Deploy separately from the application |
| **Best for** | Small to medium apps, development, testing | Large-scale apps with many users |
| **Scalability** | Limited | Highly scalable |
| **Concurrency** | Limited | Full concurrency control |
| **Server required?** | No (serverless, self-contained) | Yes |

### When to Switch

- **Start with SQLite** for new projects - it's fast and easy
- **Switch to a production DB** when your app has tens of thousands of users or needs better concurrency
- You can always migrate later - the SQLAlchemy models stay the same; only the connection string changes

> **Tip:** Starting with SQLite doesn't lock you in. You can scale up to PostgreSQL or MySQL when the time comes.

---

## PostgreSQL Introduction

### What is PostgreSQL?

An **open-source relational database management system** that runs on a server. It's secure, highly scalable, and built for production workloads.

| Trait | PostgreSQL |
|------|------------|
| Open source | Yes |
| Server-based | Yes (opposite of SQLite's serverless model) |
| Scalable | Very - handles large numbers of users |
| Secure | Yes |

### Who Uses PostgreSQL?

Apple, Reddit, Twitch - among many others.

### What We'll Do

1. Install PostgreSQL (Windows and Mac)
2. Create a database and tables using pgAdmin
3. Connect our FastAPI app to PostgreSQL

### PostgreSQL Installation (Windows)

#### Step-by-Step

1. Go to **postgresql.org** → **Download** → **Windows**
2. Download the **installer** (e.g., version X.x - newer versions are fine too)
3. Run the installer:
   - **Install location**: `C:\Program Files\PostgreSQL\14`
   - **Components**: Check all (Server, pgAdmin 4, Stack Builder, Command Line Tools)
   - **Data directory**: Default
   - **Password**: Set a superuser password (e.g., `test1234!`)
   - **Port**: `5432` (default)
   - **Locale**: Default
4. Click **Next** through the installation - it may take several minutes
5. When complete, **Stack Builder** may launch - you can **cancel** it (not needed for this course)
6. Open **pgAdmin 4** (the GUI for managing PostgreSQL):
   - Enter the master password you set during installation
   - Navigate to **Servers** → enter the password again → check **Save password**

#### pgAdmin 4

pgAdmin 4 is the visual interface for PostgreSQL - similar to how MySQL Workbench is for MySQL. You'll use it to create databases, tables, and run SQL queries.

### PostgreSQL Installation (Mac)

#### Step-by-Step

1. Go to **postgresql.org** → **Download** → **Mac**
2. Scroll to **Postgres.app** - the simplest way to install PostgreSQL on macOS
3. Download the **Universal** version
4. Open the `.dmg` file → drag Postgres to **Applications**
5. Open Postgres.app:
   - Click **Initialize** to create the data directory
   - PostgreSQL is now running (shown in the menu bar)
6. Run the terminal command shown in Postgres.app's setup instructions (adds PostgreSQL to your PATH)
7. Download and install **pgAdmin 4** for Mac:
   - Go to **pgadmin.org** → Download → Mac OS
   - Open the `.dmg` → drag pgAdmin to **Applications**
   - Open pgAdmin → set a master password

#### pgAdmin 4 (Mac)

Same as Windows - this is where you'll create your database, tables, and run queries.

---

## PostgreSQL Create Database & Tables

### Step 1 - Register a Server

In pgAdmin:

1. Right-click **Servers** → **Register** → **Server**
2. **Name**: `TodoApplicationServer`
3. **Connection** tab:
   - Host: `localhost`
   - Port: `5432`
   - Password: your PostgreSQL password (e.g., `test1234!`)
4. Click **Save**

### Step 2 - Verify the Superuser

1. Expand **Login/Group Roles**
2. Right-click **postgres** → **Properties** → **Privileges**
3. Confirm it has **Super user** privileges

> If no superuser exists, right-click **Login/Group Roles** → **Create** → give it a name and enable all default privileges.

### Step 3 - Create the Database

1. Right-click **Databases** → **Create** → **Database**
2. **Name**: `TodoApplicationDatabase`
3. **Owner**: `postgres` (the superuser)
4. Click **Save**
5. Confirm you're connected (right-click → **Connect Database** if not auto-connected)

### Step 4 - Create Tables with SQL

Open the **Query Tool** (top-left icon) and paste the SQL:

```sql
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id SERIAL,
    email VARCHAR(200) DEFAULT NULL,
    username VARCHAR(45) DEFAULT NULL,
    first_name VARCHAR(45) DEFAULT NULL,
    last_name VARCHAR(45) DEFAULT NULL,
    hashed_password VARCHAR(200) DEFAULT NULL,
    is_active BOOLEAN DEFAULT NULL,
    role VARCHAR(45) DEFAULT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS todos;
CREATE TABLE todos (
    id SERIAL,
    title VARCHAR(200) DEFAULT NULL,
    description VARCHAR(200) DEFAULT NULL,
    priority INTEGER DEFAULT NULL,
    complete BOOLEAN DEFAULT NULL,
    owner_id INTEGER DEFAULT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id) REFERENCES users (id)
);
```

Click **Execute** (the play button). Right-click **Tables** → **Refresh** to see both tables.

### PostgreSQL-Specific Notes

| Feature | PostgreSQL Syntax |
|---------|-------------------|
| Auto-incrementing ID | `SERIAL` (one keyword replaces multiple options) |
| String type | `VARCHAR(n)` |
| Boolean type | `BOOLEAN` |
| Foreign key | `FOREIGN KEY (owner_id) REFERENCES users (id)` |

### Verify the Tables

```sql
SELECT * FROM todos;   -- shows columns: id, title, description, priority, complete, owner_id
SELECT * FROM users;   -- shows columns: id, email, username, first_name, last_name, hashed_password, is_active, role
```

Both tables will be empty - no records yet.

---

## PostgreSQL Connect to FastAPI

### Step 1 - Install the PostgreSQL Driver

```bash
pip install psycopg2-binary
```

> This library lets SQLAlchemy communicate with PostgreSQL.

### Step 2 - Update the Connection String

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:test1234!@localhost/TodoApplicationDatabase"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

### What Changed from SQLite

| Before (SQLite) | After (PostgreSQL) |
|-----------------|---------------------|
| `sqlite:///./todosapp.db` | `postgresql://postgres:PASSWORD@localhost/todo_application_database` |
| `connect_args={"check_same_thread": False}` | **Removed** (SQLite-only setting) |

### Connection String Format

```
postgresql://USERNAME:PASSWORD@HOST/DATABASE_NAME
```

### Step 3 - Test It

1. Run `uvicorn main:app --reload`
2. Open the Swagger UI at `/docs`
3. **POST /auth** - create a user (e.g., `admin`, admin role)
4. Create a second user (e.g., `tagore`, no admin role)
5. **Authorize** with the lock icon
6. **POST /todo** - create a to-do
7. Check pgAdmin: `SELECT * FROM users;` shows 2 records, `SELECT * FROM todos;` shows 1 record with `owner_id = 1`

> **Cleanup:** Once PostgreSQL is connected, you can delete the old `todosapp.db` SQLite file. To switch back to SQLite, just change the connection string again.

---

## MySQL Introduction

### What is MySQL?

An **open-source relational database management system** that runs on a server. Like PostgreSQL, it's secure, scalable, and built for production.

| Trait | MySQL |
|-------|-------|
| Open source | Yes |
| Server-based | Yes |
| Scalable | Very |
| Secure | Yes |

### Who Uses MySQL?

Facebook, YouTube, Tesla - among many others.

### SQLite vs MySQL

| SQLite | MySQL |
|--------|-------|
| Serverless, self-contained | Runs on a server |
| Development / testing | Production |
| Limited scalability | Highly scalable |

### MySQL Installation (Windows)

#### Step-by-Step

1. Go to **mysql.com** → **Developer Zone** → **Downloads** → **MySQL Community Server**
2. Find **MySQL Installer for Windows** → click **Go to Download Page**
3. Download the **Windows (x86, 32-bit) MSI Installer** (web installer - lightweight)
4. Click **No thanks, just start my download** (skip the login)
5. Run the installer:
   - **Setup Type**: Developer Default
   - Click **Next** through path checks and requirements
   - Click **Execute** to download all components (Server, Workbench, Shell, Router)
   - If you get "Try again" errors, keep clicking - as long as you see checkmarks, it's working
   - Click **Execute** again to install all downloaded components
6. **Configuration**:
   - **Type and Networking**: Port `3306` (default) → Next
   - **Authentication**: Use strong password encryption (recommended)
   - **Root password**: Set a password (e.g., `test1234!`)
   - **Create a user**: Username `admin`, role `DB Admin`, same password
   - **Windows Service**: Optionally disable start on system startup
7. Click **Execute** → **Finish** → **Next** through router config (skip)
8. **Samples and Examples**: Test login with `root` / `test1234!` → Check → connection successful → Execute → Finish

#### MySQL Workbench

Launch **MySQL Workbench** → double-click **Local instance MySQL80** → enter root password → you're in. The left panel shows your schemas (databases).

### MySQL Installation (Mac)

#### Step-by-Step

1. Go to **mysql.com** → **Developer Zone** → **Downloads** → **MySQL Community Server**
2. Select **macOS** (should auto-detect)
3. Download the correct **DMG archive** for your chip:
   - **ARM** = M1/M2/M3 chips
   - **x86** = Intel chips
4. Click **No thanks, just start my download**
5. Open the `.dmg` → run the installer:
   - Click **Continue** → **Install** → enter your computer password
   - On Intel machines, you may be prompted to set a **root password** (e.g., `test1234!`)
   - Click **Finish** and start MySQL Server
6. Verify: **System Preferences** → **MySQL** → confirm the server is running
7. Download **MySQL Workbench for Mac**:
   - Go to **mysql.com** → search "MySQL Workbench for Mac"
   - Download the DMG → drag to **Applications**
   - Open Workbench → double-click **Local instance** → enter root password → you're in

---

## MySQL Create Database & Tables

### Step 1 - Create a Schema (Database)

1. In MySQL Workbench, right-click in the **Schemas** panel → **Create Schema**
2. **Name**: `TodoApplicationDatabase`
3. Click **Apply** → **Apply** → **Close**
4. Double-click the schema to make it active (it becomes **bold/highlighted**)

### Step 2 - Create Tables with SQL

Paste the following SQL into a query tab:

```sql
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT(11) NOT NULL AUTO_INCREMENT,
    email VARCHAR(200) DEFAULT NULL,
    username VARCHAR(45) DEFAULT NULL,
    first_name VARCHAR(45) DEFAULT NULL,
    last_name VARCHAR(45) DEFAULT NULL,
    hashed_password VARCHAR(200) DEFAULT NULL,
    is_active BOOLEAN DEFAULT NULL,
    role VARCHAR(45) DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS todos;
CREATE TABLE todos (
    id INT(11) NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) DEFAULT NULL,
    description VARCHAR(200) DEFAULT NULL,
    priority INT(11) DEFAULT NULL,
    complete BOOLEAN DEFAULT NULL,
    owner_id INT(11) DEFAULT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id) REFERENCES users (id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
```

Click the **lightning bolt** (execute) icon. Right-click **Tables** → **Refresh All** to see both tables.

### MySQL-Specific Notes

| Feature | MySQL Syntax |
|---------|-------------|
| Auto-incrementing ID | `INT(11) NOT NULL AUTO_INCREMENT` |
| String type | `VARCHAR(n)` |
| Boolean type | `BOOLEAN` |
| Storage engine | `ENGINE=InnoDB` (default) |
| Character set | `DEFAULT CHARSET=latin1` (default) |
| Foreign key | `FOREIGN KEY (owner_id) REFERENCES users (id)` |

### PostgreSQL vs MySQL Table Syntax

| Concept | PostgreSQL | MySQL |
|---------|-----------|-------|
| Auto-increment | `SERIAL` | `INT(11) NOT NULL AUTO_INCREMENT` |
| Engine/charset | Not needed | `ENGINE=InnoDB DEFAULT CHARSET=latin1` |
| Primary key | `PRIMARY KEY (id)` | `PRIMARY KEY (id)` |
| Foreign key | `FOREIGN KEY (owner_id) REFERENCES users (id)` | Same |

### Verify the Tables

```sql
SELECT * FROM todos;   -- columns: id, title, description, priority, complete, owner_id
SELECT * FROM users;   -- columns: id, email, username, first_name, last_name, hashed_password, is_active, role
```

Both tables will be empty.

---

## MySQL Connect to FastAPI

### Step 1 - Install the MySQL Driver

```bash
pip install pymysql
```

### Step 2 - Update the Connection String

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:test1234!@127.0.0.1:3306/TodoApplicationDatabase"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

### What Changed from SQLite

| Before (SQLite) | After (MySQL) |
|-----------------|---------------|
| `sqlite:///./todosapp.db` | `mysql+pymysql://root:PASSWORD@127.0.0.1:3306/todo_application_database` |
| `connect_args={"check_same_thread": False}` | **Removed** (SQLite-only setting) |

### Connection String Format

```
mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

### Step 3 - Test It

1. Run `uvicorn main:app --reload`
2. Open the Swagger UI at `/docs`
3. **POST /auth** - create `admin` (admin) and `tagore` (non-admin)
4. **Authorize** with the lock icon using `admin` / `<Password>`
5. **POST /todo** - create a to-do (e.g., "Learn FastAPI", priority 5, complete = true)
6. Check MySQL Workbench: `SELECT * FROM users;` shows 2 records, `SELECT * FROM todos;` shows 1 record with `owner_id = 1`

> **Cleanup:** Once MySQL is connected, delete the old `todosapp.db` SQLite file. To switch back, just change the connection string.