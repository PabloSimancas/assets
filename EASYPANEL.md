
## ☁️ EasyPanel Deployment

This project is optimized for deployment on [EasyPanel](https://easypanel.io/).

### 1. Service Structure
Instead of deploying the root `docker-compose.yml`, configure 3 separate services:

1.  **Database**: Native PostgreSQL Service.
2.  **Backend**: Dockerfile Build (Context: `./backend`).
3.  **Frontend**: Dockerfile Build (Context: `./frontend`).

### 2. Configuration Details

#### 📦 Database (PostgreSQL)
- Create a definition in EasyPanel.
- Note the **Host**, **User**, **Password**, and **Database Name** from the connection details.

#### ⚙️ Backend Service
- **Build Settings**:
    - Build Type: `Dockerfile`
    - Context Directory: `./backend`
    - Dockerfile Path: `Dockerfile`
- **Network / Ports**:
    - Container Port: `8000` (Crucial: Change default 80 to 8000)
- **Environment Variables**:
    - `DATABASE_URL`: `postgresql://postgres:YOUR_PASSWORD@YOUR_DB_HOST:5432/YOUR_DB_NAME`
- **Domains**:
    - Add a domain (e.g., `api.assets.easypanel.host`).
    - **Verify Path/Port**: Ensure the domain routes traffic to port **8000**.

#### 🎨 Frontend Service
- **Build Settings**:
    - Build Type: `Dockerfile`
    - Context Directory: `./frontend`
    - Dockerfile Path: `Dockerfile`
- **Network / Ports**:
    - Container Port: `3000`
- **Environment Variables**:
    - `NEXT_PUBLIC_API_URL`: The **public HTTPS URL** of your backend (e.g., `https://api.assets.easypanel.host/api/v1`).
    - *Note: Don't forget the `/api/v1` suffix.*

---

## 🔧 Deployment Troubleshooting & Known Issues

### ❌ Error: "Invariant failed" or Container Crash
**Symptom**: Deployment builds successfully but crashes immediately with an obscure error.
**Cause**: **Windows Line Endings (CRLF)**. If the `start.sh` file was saved on Windows, the Linux container cannot execute it (`bad interpreter`).
**Solution**:
- The project `Dockerfile` now includes `dos2unix` to automatically fix this during build.
- If issues persist, ensure `backend/start.sh` is saved with **LF** (Unix) line endings in your editor.

### ❌ Error: "unknown instruction: services"
**Cause**: EasyPanel is trying to read `docker-compose.yml` as a Dockerfile.
**Solution**: Change the "Build Type" in EasyPanel to "Dockerfile" and set the context to `./backend` or `./frontend` respectively.

### ❌ Frontend cannot connect to Backend
**Symptoms**: Charts don't load, "Network Error".
**Checklist**:
1.  Is `NEXT_PUBLIC_API_URL` set?
2.  Does it start with `https://`?
3.  Does it end with `/api/v1`?
4.  **Crucial**: Does the Backend Domain in EasyPanel point to port **8000**? (Default is 80, which won't work).
