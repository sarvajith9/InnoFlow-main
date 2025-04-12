# InnoFlow  
A Visual Tool for Building AI Agents (Django Edition)

### 📜 Commit Message Rules Guide

This guide explains how to write clear, structured commit messages using **commitlint** and the **Conventional Commits** standard, adapted specifically for the **Django + Python** ecosystem.

---

## 🔹 **Commit Message Format**

A valid commit message must follow this format:

```plaintext
<type>: <description>
```

### ✅ **Examples**

```
feat: Add agent builder interface
fix: Resolve issue with task execution logic
docs: Update README with setup instructions
```

---

## 🔹 **Allowed Commit Types**

Each commit must start with one of the following **valid types**:

| Type       | Meaning                                                  |
|------------|----------------------------------------------------------|
| `feat`     | A new feature (e.g., new model, view, or API endpoint)   |
| `fix`      | A bug fix                                                |
| `docs`     | Documentation changes (README, docstrings, comments)     |
| `style`    | Code formatting only (Black, isort, no logic changes)    |
| `refactor` | Refactoring code (no bug fix or feature addition)        |
| `perf`     | Performance improvements (e.g., optimized DB queries)    |
| `test`     | Adding or modifying tests                                |
| `build`    | Changes to build tools or dependencies (Docker, etc.)    |
| `ci`       | CI/CD pipeline changes (GitHub Actions, Jenkins, etc.)   |
| `chore`    | Routine tasks (e.g., version bump, updating packages)    |
| `revert`   | Reverting a previous commit                              |

🚫 **Invalid Commit Types (Blocked)**

```
update: Improve agent rendering performance  ❌
change: Modify URL patterns for dashboard     ❌
```

---

## 🔹 **Subject Formatting Rules**

✅ **Do**:  
✔ Start with a **capital letter**  
✔ Keep message **concise and meaningful** (max 72 characters)  

🚫 **Don't**:  
❌ Use **lowercase** for the first word (`feat: add new endpoint`)  
❌ Use **ALL CAPS** (`fix: FIX CONNECTION ISSUE`)  
❌ End with a **period** (`docs: Add contribution guide.`)

---

## 🔹 **Why Follow These Rules?**

✔ Maintains a **clean and consistent Git history**  
✔ Supports **automated changelogs and semantic versioning**  
✔ Makes collaboration easier and **code reviews faster**  

---

By following these rules, your contributions to **InnoFlow** will be clean, meaningful, and future-proof! 🚀

---

## ✅ Running Tests (Django)

To run all tests:

```bash
python manage.py test
```

Or with coverage reporting:

```bash
coverage run manage.py test
coverage report
```

---

## 🧪 Test Structure Overview

| Test Type           | What to Test?                                  | Tools Used             |
|---------------------|------------------------------------------------|------------------------|
| **Unit Tests**      | Models, Serializers, Utilities                 | `unittest`, `pytest`   |
| **Integration Tests** | Views, APIs, and Services                      | `pytest-django`        |
| **Database Tests**  | ORM queries, migrations, constraints            | Django TestCase        |
| **Utility Tests**   | Custom validators, helpers, formatters         | `pytest` or `unittest` |
| **Fixtures**        | Mock data (users, agents, tasks, etc.)         | Python, JSON, or YAML  |

---

## ✅ API Documentation

If you're using **DRF with drf-yasg** or **drf-spectacular**, Swagger UI is served at:

```bash
http://localhost:8000/swagger/
```

It includes:
- Full list of available API endpoints  
- Request/response schemas  
- Status codes  
- Example payloads  

---

By following these conventions and testing practices, **InnoFlow** will stay robust, scalable, and developer-friendly. 💡💻

---
