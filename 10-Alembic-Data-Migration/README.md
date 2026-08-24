# Alembic Data Migration

## Table of Contents

- [What is Alembic?](#what-is-alembic)
- [Alembic Commands Overview](#alembic-commands-overview)
- [Installation & Setup](#installation--setup)
- [Alembic Revisions Overview](#alembic-revisions-overview)
- [Revision Upgrade - Adding a Column](#revision-upgrade---adding-a-column)
- [Revision Downgrade - Removing a Column](#revision-downgrade---removing-a-column)

---

## What is Alembic?

**Alembic** is a lightweight database migration tool for SQLAlchemy. It lets you modify database tables **after** they've already been created and filled with data - without deleting the table or losing any records.

### The Core Problem It Solves

SQLAlchemy can only **create** new tables - it cannot **enhance** existing ones.

| Scenario | SQLAlchemy | Alembic |
|----------|------------|---------|
| Table doesn't exist | Creates it automatically | Not needed |
| Table exists, you want to add a column | Cannot do it | Adds the column safely |
| Table exists, you want to remove a column | Cannot do it | Removes the column safely |

### Our Example

We have a `users` table with existing data:

| id | email | first_name | last_name | ... |
|----|-------|------------|-----------|-----|
| 1 | tagore8661@gmail.com | TAGORE | GANUGA | ... |

We want to add a `phone_number` column **without** deleting the table or losing any data. Alembic makes this possible.

### Why Do We Need It?

#### Without Alembic (The Manual Way)

1. Add `phone_number = Column(String)` to your model
2. Start the app → **Error!** SQLAlchemy tries to query `phone_number` but the column doesn't exist in the database
3. The only fix is to **delete the entire database** and let SQLAlchemy recreate the tables from scratch
4. **All existing data is lost**

#### With Alembic

1. Add `phone_number = Column(String)` to your model
2. Create an Alembic revision with an `upgrade` function that adds the column
3. Run `alembic upgrade <revision_id>`
4. The column is added to the existing table - **no data is lost**

#### What Happens Without Alembic

```
Add phone_number to model → Start app → Query fails:

  "no such column: users.phone_number"
```

The model defines the SQL query SQLAlchemy writes, but it does **not** modify the actual database table. The table already exists, so SQLAlchemy skips creation.

---

## Alembic Commands Overview

### Key Commands

| Command | Purpose |
|---------|---------|
| `pip install alembic` | Install Alembic |
| `alembic init <folder_name>` | Initialize a new migration environment |
| `alembic revision -m "message"` | Create a new revision file for a migration |
| `alembic upgrade <revision_id>` | Run the upgrade migration |
| `alembic downgrade -1` | Revert the last migration |

### Command Flow

```
1. pip install alembic
         ↓
2. alembic init alembic         → creates the migration environment
         ↓
3. alembic revision -m "..."    → creates a new revision file
         ↓
4. Write upgrade() and downgrade() functions in the revision file
         ↓
5. alembic upgrade <revision_id>  → applies the upgrade
         ↓
6. alembic downgrade -1          → reverts the last upgrade (if needed)
```

---

## Installation & Setup

### Step 1 - Install Alembic

```bash
pip install alembic
```

### Step 2 - Initialize the Migration Environment

```bash
alembic init alembic
```

*This creates two items in your project directory:*

```
TodoApp/
├── alembic.ini          ← configuration file
├── alembic/             ← migration directory
│   ├── env.py           ← environment config (needs edits)
│   ├── README           ← generic info
│   ├── script.py.mako   ← template for revision files
│   └── versions/        ← where revision files are stored
│       └── <revision_id>_<message>.py
│                     :
├── main.py
├── database.py
├── models.py
└── routers/
```

### Step 3 - Configure `alembic.ini`

Find the line `sqlalchemy.url = driver://user:pass@localhost/dbname` and replace it with your database URL:

```ini
# For SQLite
sqlalchemy.url = sqlite:///./todosapp.db

# For PostgreSQL
sqlalchemy.url = postgresql://postgres:test1234!@localhost/TodoApplicationDatabase

# For MySQL
sqlalchemy.url = mysql+pymysql://root:test1234!@127.0.0.1:3306/TodoApplicationDatabase
```

> Copy this from your `database.py` file's `SQLALCHEMY_DATABASE_URL`.

### Step 4 - Configure `alembic/env.py`

*Make two changes:*

**Change 1 - Import your models:**

```python
# Near the top of env.py
import models
```

**Change 2 - Set the target metadata:**

Find the line `target_metadata = None` and change it to:

```python
target_metadata = models.Base.metadata
```

> `models.Base.metadata` tells Alembic about all your table definitions so it can compare them against the actual database.

*What NOT to Change in `env.py`:*

| Line | Action |
|------|--------|
| `config = context.config` | Leave as-is |
| `fileConfig(config.config_file_name)` | Remove the surrounding `if` statement, keep the line itself |
| Offline/online migration sections | Leave as-is |

---

## Alembic Revisions Overview

### What is an Alembic Revision?

An **Alembic revision** is a Python file that contains the code to upgrade (and optionally downgrade) your database. Each revision has a unique **revision ID** (a string of letters and numbers).

### Creating an Alembic Revision

```bash
alembic revision -m "create phone number for user column"
```

This creates a new file inside `alembic/versions/`:

```
alembic/versions/
└── a1b2c3d4e5f6_create_phone_number_for_user_column.py
```

### Revision File Structure

```python
"""create phone number for user column

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-08-20 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Write upgrade code here
    pass

def downgrade() -> None:
    # Write downgrade code here
    pass
```

| Import | Purpose |
|--------|---------|
| `op` | Alembic operations (add_column, drop_column, etc.) |
| `sa` | SQLAlchemy types (Column, String, Integer, Boolean, etc.) |

### Upgrade vs Downgrade

| Function | Direction | Example |
|----------|-----------|---------|
| `upgrade()` | Forward - applies a change | Add a column |
| `downgrade()` | Backward - reverts a change | Remove a column |

---

## Revision Upgrade - Adding a Column

### The Upgrade Function

Inside the revision file, write:

```python
def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('phone_number', sa.String(), nullable=True)
    )
```

### Why `nullable=True`?

Existing users don't have a phone number yet. Setting `nullable=True` allows the column to be `NULL` for all existing records. If you set `nullable=False`, the migration would fail because there's no default value for existing rows.

| Parameter | Value | Reason |
|-----------|-------|--------|
| Table name | `'users'` | The table we're modifying |
| Column name | `'phone_number'` | The new column |
| Type | `sa.String()` | Stores a text string |
| `nullable` | `True` | Existing rows have no phone number yet |

### Running the Upgrade

```bash
alembic upgrade a1b2c3d4e5f6
```

Replace `a1b2c3d4e5f6` with your actual revision ID (found at the top of the revision file).

### What Happens

```
1. Alembic reads the revision file
         ↓
2. Runs upgrade() → op.add_column('users', ...)
         ↓
3. The 'phone_number' column is added to the users table
         ↓
4. All existing data is preserved (phone_number = NULL for all rows)
```

### After the Upgrade

Add the column to your SQLAlchemy model so the application knows about it:

```python
# models.py
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
    phone_number = Column(String)    # ← newly added
```

Now when you query users, `phone_number` appears in the response (as `null` for existing users).

### Verification

| Check | Result |
|-------|--------|
| App starts without errors | Yes |
| Login works | Yes |
| `GET /auth/user` returns `phone_number: null` | Yes |
| Existing data (email, name, etc.) | Preserved |

---

## Revision Downgrade - Removing a Column

### The Downgrade Function

Inside the same revision file, write:

```python
def downgrade() -> None:
    op.drop_column('users', 'phone_number')
```

| Parameter | Value | Reason |
|-----------|-------|--------|
| Table name | `'users'` | The table we're modifying |
| Column name | `'phone_number'` | The column to remove |

### Running the Downgrade

```bash
alembic downgrade -1
```

The `-1` means "revert the **last** migration that was applied."

### What Happens

```
1. Alembic reads the revision file
         ↓
2. Runs downgrade() → op.drop_column('users', 'phone_number')
         ↓
3. The 'phone_number' column is removed from the users table
         ↓
4. All other data is preserved (only phone_number data is lost)
```

> **Warning:** If any users had phone numbers stored, that data is deleted when the column is dropped. Only downgrade when there's a bug or something is breaking the application.

### After the Downgrade

If you downgraded, you must also **remove** `phone_number` from your `models.py` - otherwise the app will crash when it tries to query a column that no longer exists:

```
Error: "no such column: users.phone_number"
```

### Re-Upgrading

If you change your mind and want the column back:

```bash
alembic upgrade a1b2c3d4e5f6
```

Same command as before - it re-applies the upgrade and the column returns.
