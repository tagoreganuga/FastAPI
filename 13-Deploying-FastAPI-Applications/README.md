# Deploying FastAPI Applications

## Table of Contents

- [Render Introduction](#render-introduction)
- [Add Requirements File](#add-requirements-file)
- [Render Setup](#render-setup)
- [PostgreSQL Production Database](#postgresql-production-database)

---

## Render Introduction

### What is Render?

**Render** is a **Platform as a Service (PaaS)** - one of the main categories of cloud computing. You pay on a per-use basis (or a flat monthly fee depending on the plan).

Render helps developers **build, run, and operate applications entirely on the cloud**. Instead of hosting your application on your personal PC through `localhost`, you let a cloud computing company handle the deployment.

### Why Use a PaaS Like Render?

| Without Render (Manual Deployment) | With Render |
|---|---|
| You manage infrastructure, code deployment, DevOps, CI/CD | Render handles infrastructure for you |
| You handle scalability and load balancing | Render handles scaling automatically |
| You focus on infrastructure + code | You focus only on code |

> Keeping developers focused on development instead of infrastructure helps a ton when trying to rapidly produce new features.

### Pricing

Pricing depends on how you want your application to perform online. For this course, the **free plan** is used. Businesses of all sizes use Render as their cloud PaaS provider.

### How Render Fits Into the Deployment Cycle

```
1. Application code → version controlled with Git
         ↓
2. Code pushed to GitHub (online hosting service)
         ↓
3. Render account connected to GitHub
         ↓
4. Render deploys changes from the master/main branch
         ↓
5. Application is live and available to all users
```

### Other Cloud Providers

| Provider | Type |
|---|---|
| **Render** | PaaS (used in this course) |
| **AWS** | IaaS / PaaS |
| **Azure** | IaaS / PaaS |
| **Google Cloud** | IaaS / PaaS |

---

## Add Requirements File

### What is a Requirements File?

A `requirements.txt` file tells any environment **all the dependencies** your application needs to run. When Render deploys your app, it reads this file and installs every dependency listed in it.

### Generate the File

```bash
pip3 freeze > requirements.txt
```

> On Windows, use `pip` instead of `pip3`.

### What It Contains

The generated file lists every installed package and its version:

```
fastapi
uvicorn
starlette
sqlalchemy
...
```

| Dependency | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server to run the app |
| `starlette` | Underlying ASGI toolkit |
| `sqlalchemy` | Database ORM |

### Commit and Push to GitHub

```bash
git add -A
git commit -m "add requirements file"
git push
```

> The requirements file **must** be on GitHub because Render will pull from your GitHub repository to deploy.

---

## Render Setup

### Step 1 - Create a Render Account

1. Go to [render.com](https://render.com)
2. Click **Get Started**
3. Sign in with **GitHub** (recommended - auto-connects to GitHub without any third-party acceptance)

### Step 2 - Create a Web Service

Render offers several service types:

| Service Type | Use Case |
|---|---|
| Static Sites | Static websites |
| **Web Services** | Full-stack web applications (what we use) |
| Private Services | Internal services |
| Background Workers | Background tasks |

Click **New Web Service** and connect your GitHub repository.

### Step 3 - Configure the Web Service

Select **Connect to GitHub** and choose your repository.

| Setting | Value | Notes |
|---|---|---|
| **Name** | `<your-app-name>` | Any name you like |
| **Root Directory** | (skip) | Leave blank |
| **Environment** | `Python 3` | Not Docker |
| **Region** | Closest to you | Reduces latency (e.g., Ohio US East) |
| **Branch** | `main` | Your deployment branch |
| **Build Command** | `pip install -r requirements.txt` | Installs all dependencies |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port 10000` | Starts the ASGI server |
| **Plan** | Free | Free tier for this course |

### The Start Command Explained

```bash
uvicorn main:app --host 0.0.0.0 --port 10000
```

| Part | Meaning |
|---|---|
| `uvicorn` | The ASGI server |
| `main:app` | The `app` object inside `main.py` |
| `--host 0.0.0.0` | Listen on all interfaces (required by Render) |
| `--port 10000` | The port Render expects |

### Step 4 - Deploy

Click **Create Web Service**. Render will:

```
1. Clone from Git
      ↓
2. Check out the commit
      ↓
3. Download and cache dependencies from requirements.txt
      ↓
4. Run the start command (uvicorn main:app --host 0.0.0.0 --port 10000)
      ↓
5. Application is live
```

> This can take a few minutes.

### If the Build Fails

On the free tier, deployments sometimes fail due to limited performance and resources.

| Fix | How |
|---|---|
| Clear build cache and redeploy | Click the manual deploy button (play icon) → **Clear build cache & deploy** |
| Review deployment scripts | Check that build and start commands are correct |

### After Deployment

- You get a **URL** for your live application
- Open it in a new tab to access your app
- If you deployed a SQLite `todosapp.db` file, you'll see existing users and todos - because the `.db` file was part of the repo

> **Note:** SQLite is a file-based database. Deploying it means the database file itself was uploaded. This is **not** suitable for production. The next step is to set up a proper PostgreSQL production database.

---

## PostgreSQL Production Database

### Why Not Use Render's PostgreSQL?

Render offers a PostgreSQL database, but on the **free plan**, databases **expire in 90 days** and are deleted if not upgraded.

| Option | Issue |
|---|---|
| Render PostgreSQL (free) | Deleted after 90 days |
| ElephantSQL (free) | Used instead - no 90-day expiry |

### Using ElephantSQL

**ElephantSQL** is a managed PostgreSQL service that offers a free tier ("Tiny Turtle").

### Step 1 - Create an ElephantSQL Account

1. Go to [elephantsql.com](https://elephantsql.com)
2. Log in (Google, GitHub, or email)

### Step 2 - Create a New Instance

| Setting | Value | Notes |
|---|---|---|
| **Name** | `deploy-database` | Any name you like |
| **Plan** | Tiny Turtle (Free) | Free tier |
| **Tag** | `demo-tag` | Optional |
| **Region** | Closest to your Render app's region | Minimizes latency (e.g., Northern Virginia / US East) |

> **Region tip:** Make sure your database region is close to your Render application region. If your Render app is in Ohio and ElephantSQL doesn't offer Ohio on the free plan, pick the closest option (e.g., Northern Virginia - both are US East).

Click **Review** → **Create Instance**.

### Step 3 - Get the Database URL

1. Open your newly created instance
2. Find the **URL** field
3. Copy the URL

### Step 4 - Update Your Application

In your `database.py` file:

```python
# Comment out the SQLite configuration
# SQLALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Uncomment and use the PostgreSQL configuration
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host/database"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
```

Paste your ElephantSQL URL:

```python
SQLALCHEMY_DATABASE_URL = "postgres://youruser:yourpassword@yourhost/yourdb"
```

> **Important:** SQLAlchemy expects `postgresql` (not `postgres`). Add `ql` to the end of the URL scheme:
>
> Change `postgres://...` to `postgresql://...`

### Step 5 - Commit and Push

```bash
git status              # see the change to database.py
git add -A
git commit -m "production database change"
git push
```

### Step 6 - What Happens During Deployment

```
1. Render detects the push to GitHub
      ↓
2. Render starts a new deployment
      ↓
3. Build runs (pip install -r requirements.txt)
      ↓
4. App starts (uvicorn main:app --host 0.0.0.0 --port 10000)
      ↓
5. SQLAlchemy connects to ElephantSQL
      ↓
6. SQLAlchemy creates all tables automatically (users, todos)
```

> SQLAlchemy automatically creates all tables when the app starts and the database is empty.

### Step 7 - Verify the Database

1. Open your deployed application URL
2. Go back to ElephantSQL → **Browser** (the SQL browser tool)
3. Run a query to list tables:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

| Table | Created By |
|---|---|
| `users` | SQLAlchemy (auto-created on startup) |
| `todos` | SQLAlchemy (auto-created on startup) |

### Final Architecture

```
GitHub Repository
      ↓ (push triggers deploy)
Render (Web Service)
      ↓ (connects to)
ElephantSQL (PostgreSQL)
      ├── users table
      └── todos table
```