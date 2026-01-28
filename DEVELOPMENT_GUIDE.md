# Development Workflow Guide

## How to Apply Code Changes

Since you are running the application in Docker, the update process depends on which part of the application you changed.

### 1. Backend Changes (Python)
The backend is configured to **auto-reload**.
- You generally **do not** need to do anything.
- When you save a file in `backend/src`, the server inside the container detects the change and restarts automatically.
- **Exception**: If you add new dependencies to `requirements.txt`, you must rebuild:
  ```powershell
  docker-compose up -d --build backend
  ```

### 2. Frontend Changes (React/Next.js)
Currently, the frontend runs as a **production build** inside Docker.
- **You MUST rebuild the container** to see changes.
- Run this command:
  ```powershell
  docker-compose up -d --build frontend
  ```

### 3. "Update All" (Easiest Way)
If you want to ensure everything is up to date, simply run:
```powershell
./update_app.ps1
```
(We have created this script for you).

## Useful Commands

- **Check Logs**:
  ```powershell
  docker-compose logs -f
  ```
- **Restart Specific Service**:
  ```powershell
  docker-compose restart backend
  ```
