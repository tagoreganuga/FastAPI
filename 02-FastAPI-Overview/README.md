# FastAPI Overview

## Table of Contents
- [What is FastAPI?](#what-is-fastapi)
- [Virtual Environments](#virtual-environments)

---

## What is FastAPI?

A **Python web framework** for building modern RESTful APIs - simple, scalable, and extensible.

**"Fast" has two meanings:**

1. **Performance** - One of the fastest web frameworks available. Data validation, serialization, auto documentation, and security are all built-in.
2. **Development Speed** - A few lines of code gives you a ready-to-deploy API.

**Key benefits:**

- ~40% fewer bugs thanks to embedded data validation
- Easy to learn, easy to use - designed with the developer in mind
- Production-ready within minutes with automatic documentation
- Built on **OpenAPI** and **JSON Schema** standards

**Docs:** [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)

### Where FastAPI Fits

```text
 User  →  Web Page (Frontend)  →  RESTful APIs  →  FastAPI Server (Business Logic + Security)
```

- The web page requests data from the server through RESTful APIs.
- FastAPI ensures the web page gets **correct and secure data**.
- FastAPI can power just the backend (RESTful API) or the full stack (backend + rendered frontend).

**Companies using FastAPI:** Netflix, Uber, Microsoft.

### Why Use a Web Framework?

You *could* write everything yourself - but why reinvent the wheel?

- Frameworks give you rapid development without reinventing security, validation, and documentation.
- Years of edge cases are already handled for you.
- You get a secure, fast application running within minutes.

---

## Virtual Environments

A **virtual environment** isolates one project's dependencies from another.

**Why?** Different projects need different packages (e.g. a FastAPI app vs. an AI project vs. an IoT project). Without isolation, dependencies clash. With it, each project is siloed and independent - even two FastAPI projects can use different versions of the same package.

**Pip** is the Python package manager (comes with Python). **`venv`** is Python's built-in tool for creating virtual environments - no extra install needed.

```bash
# Check pip version
python3 -m pip --version   # Mac
python -m pip --version    # Windows
```

### Installation - Windows

```bash
# 1. Create project folder
cd Documents
mkdir FastAPI
cd FastAPI

# 2. Create virtual environment
python -m venv fastapienv

# 3. Activate it
fastapienv\Scripts\activate.bat

# 4. Install packages
pip install fastapi
pip install "uvicorn[standard]"

# 5. Verify
pip list   # should show fastapi and uvicorn

# 6. Deactivate when done
deactivate
```

> Active when you see `(fastapienv)` before your prompt.

### Installation - Mac

```bash
# 1. Create project folder
cd Documents
mkdir FastAPI
cd FastAPI

# 2. Create virtual environment
python3 -m venv fastapienv

# 3. Activate it
source fastapienv/bin/activate

# 4. Install packages
pip install fastapi
pip install "uvicorn[standard]"

# 5. Verify
pip list   # should show fastapi and uvicorn

# 6. Deactivate when done
deactivate
```

> Active when you see `(fastapienv)` before your prompt. Inside the venv, use `pip` (not `pip3`).


### Key terms:

| Term | Meaning |
| --- | --- |
| Web Framework | Software that simplifies building web apps and APIs |
| RESTful API | An API that follows REST principles for web communication |
| Virtual Environment | An isolated Python environment for project-specific dependencies |
| Pip | Python's package manager |
| venv | Python's built-in virtual environment tool |
| Uvicorn | ASGI web server that runs FastAPI apps |
| OpenAPI | Spec for machine-readable API interface files |
| JSON Schema | Vocabulary for annotating and validating JSON |
