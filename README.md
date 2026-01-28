
# ASSETS Dashboard

A modern, real-time assets analytics dashboard for tracking cryptocurrencies, commodities, and market indices. Built with Next.js, FastAPI, and PostgreSQL.

![Dashboard Preview](./Captura%20de%20pantalla%202026-01-26%20210047.png)

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
  - [VPS Deployment](#vps-deployment)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)

---

## ✨ Features

- **Real-time Asset Tracking**: Monitor BTC, ETH, Gold, Silver, SPX, and major stocks
- **Interactive Charts**: Beautiful area charts with gradient fills and tooltips
- **Order Book Visualization**: Live bid/ask spreads and market depth
- **Dynamic Watchlist**: Click-to-select assets with smooth transitions
- **Market Insights**: Sentiment analysis and trend indicators
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark Mode**: Professional trading platform aesthetic

---

## 🛠 Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Pydantic** - Data validation

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **TanStack Query** - Data fetching and caching
- **Recharts** - Chart visualization
- **Lucide React** - Icon library

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Caddy** - Reverse proxy with automatic HTTPS
- **Uvicorn** - ASGI server

---

## 🏗 Architecture

This project follows **Clean Architecture** principles:

```
backend/
├── src/
│   ├── domain/          # Business entities and rules
│   ├── application/     # Use cases and DTOs
│   ├── infrastructure/  # Database, repositories
│   └── interfaces/      # API routers, dependency injection

frontend/
├── app/                 # Next.js pages and layouts
├── features/            # Feature-based modules
├── lib/                 # API client and utilities
└── public/              # Static assets
```

---

## 🚀 Getting Started

### Prerequisites

**For Local Development:**
- Python 3.11 or higher
- Node.js 18+ and npm
- PostgreSQL 15+ (or use Docker)

**For Docker/VPS Deployment:**
- Docker 24+
- Docker Compose 2.20+

---

## 💻 Local Development

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd assets_dashboard
```

### 2. Backend Setup

```bash
#find other process in the port 8000
netstat -ano | findstr :8000

#kill the process
taskkill /F /PID 144456

# Navigate to backend directory
C:\Users\ASUS\Desktop\Areas\Código\assets_dashboard\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
# On Windows PowerShell:
$env:DATABASE_URL="sqlite:///./test.db"
$env:PYTHONPATH="."

# On Linux/Mac:
export DATABASE_URL="sqlite:///./test.db"
export PYTHONPATH="."

# Seed the database with sample data
python seed.py

# Run the backend server
python -m uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8002 --reload
```

The backend API will be available at: **http://localhost:8002**

API Documentation: **http://localhost:8002/docs**

### 3. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set environment variable
# On Windows PowerShell:
$env:NEXT_PUBLIC_API_URL="http://localhost:8002/api/v1"

# On Linux/Mac:
export NEXT_PUBLIC_API_URL="http://localhost:8002/api/v1"

# Run the development server
npm run dev
```

The frontend will be available at: **http://localhost:3002** (or 3000 if running locally without Docker)

---

## 🐳 Docker Deployment

### Local Docker Setup

```bash
C:\Users\ASUS\Desktop\Areas\Código\assets_dashboard

# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d --build
```

**Services will be available at:**
- Frontend: http://localhost:3002
- Backend API: http://localhost:8002
- Reverse Proxy: http://localhost:80
- PostgreSQL: localhost:5434

### Seed Database in Docker

```bash
# Execute seed script inside the backend container
docker compose exec backend python seed.py
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v
```

---

## 🌐 VPS Deployment

### Prerequisites on VPS

1. **Ubuntu 22.04 LTS** (or similar Linux distribution)
2. **Docker and Docker Compose installed**
3. **Domain name** (optional, for HTTPS)
4. **Firewall configured** to allow ports 80 and 443

### Step 1: Install Docker on VPS

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone Repository on VPS

```bash
# Install git if not present
sudo apt install git -y

# Clone your repository
git clone <your-repo-url>
cd assets_dashboard
```

### Step 3: Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit environment variables
nano .env
```

**Important .env settings for production:**

```env
# Database
DB_USER=postgres
DB_PASSWORD=<STRONG_PASSWORD_HERE>
DB_NAME=assets_db

# Backend
DATABASE_URL=postgresql://postgres:<STRONG_PASSWORD_HERE>@db:5432/assets_db
ENV=production

# Frontend
NEXT_PUBLIC_API_URL=http://your-domain.com/api/v1
# Or if using IP: http://YOUR_VPS_IP/api/v1
```

### Step 4: Configure Caddy for Your Domain

Edit `caddy/Caddyfile`:

```bash
nano caddy/Caddyfile
```

**For domain with HTTPS:**

```caddyfile
your-domain.com {
    reverse_proxy /api/* backend:8000
    reverse_proxy /* frontend:3000
}
```

**For IP address (HTTP only):**

```caddyfile
:80 {
    reverse_proxy /api/* backend:8000
    reverse_proxy /* frontend:3000
}
```

### Step 5: Deploy with Docker Compose

```bash
# Build and start services
docker compose up -d --build

# Seed the database
docker compose exec backend python seed.py

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### Step 6: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH (if not already allowed)

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 7: Access Your Application

- **With domain**: https://your-domain.com
- **With IP**: http://YOUR_VPS_IP

### Maintenance Commands

```bash
# Update application
cd assets_dashboard
git pull
docker compose up -d --build

# View logs
docker compose logs -f [service_name]

# Restart specific service
docker compose restart backend
docker compose restart frontend

# Backup database
docker compose exec db pg_dump -U postgres assets_db > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20260127.sql | docker compose exec -T db psql -U postgres assets_db

# Clean up unused Docker resources
docker system prune -a
```

---

## 📚 API Documentation

### Base URL

- Local: `http://localhost:8000/api/v1`
- Production: `https://your-domain.com/api/v1`

### Endpoints

#### 1. List All Assets

```http
GET /api/v1/assets
```

**Response:**
```json
[
  {
    "symbol": "BTC",
    "name": "Bitcoin",
    "category": "Crypto"
  },
  {
    "symbol": "ETH",
    "name": "Ethereum",
    "category": "Crypto"
  }
]
```

#### 2. Get Asset Detail

```http
GET /api/v1/assets/{symbol}
```

**Parameters:**
- `symbol` (path) - Asset symbol (e.g., BTC, ETH, GOLD)

**Response:**
```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "category": "Crypto",
  "current_price": 65000.00,
  "change_24h": 2.45,
  "history": [
    {
      "price": 65000.00,
      "timestamp": "2026-01-27T14:00:00Z"
    }
  ]
}
```

#### 3. Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:00:00Z"
}
```

### Interactive API Docs

Visit `/docs` for Swagger UI documentation:
- Local: http://localhost:8000/docs
- Production: https://your-domain.com/docs

---

## 📁 Project Structure

```
assets_dashboard/
├── backend/
│   ├── src/
│   │   ├── application/
│   │   │   ├── dtos/              # Data Transfer Objects
│   │   │   ├── ports/             # Repository interfaces
│   │   │   └── use_cases/         # Business logic
│   │   ├── domain/
│   │   │   ├── entities/          # Domain models
│   │   │   └── services/          # Domain services
│   │   ├── infrastructure/
│   │   │   ├── database/          # DB models and session
│   │   │   └── repositories/      # Repository implementations
│   │   └── interfaces/
│   │       └── api/
│   │           ├── routers/       # API endpoints
│   │           └── main.py        # FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py                    # Database seeding script
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Home page
│   │   ├── providers.tsx          # React Query provider
│   │   └── globals.css            # Global styles
│   ├── features/
│   │   └── assets/
│   │       ├── components/        # Asset-related components
│   │       ├── hooks/             # Custom React hooks
│   │       └── types/             # TypeScript types
│   ├── lib/
│   │   └── apiClient.ts           # Axios configuration
│   ├── public/                    # Static files
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
│
├── caddy/
│   └── Caddyfile                  # Reverse proxy config
│
├── docker-compose.yml             # Multi-container setup
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

---

## 🔐 Environment Variables

### Backend (.env or environment)

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/dbname
# Or for SQLite: sqlite:///./test.db

# Application
ENV=development  # or production
PYTHONPATH=.

# Optional: Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env.local or environment)

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Docker Compose (.env)

```env
# Database
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=assets_db

# Automatically used by services
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🆘 Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Kill the process or change the port in docker-compose.yml
```

**2. Database connection errors**
```bash
# Check if PostgreSQL is running
docker compose ps

# View database logs
docker compose logs db

# Reset database
docker compose down -v
docker compose up -d
```

**3. Frontend can't connect to backend**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in backend
- Ensure backend is running and accessible

**4. Docker build fails**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache
```

**5. Docker build error: "/app/.next/standalone": not found**
- Ensure `output: "standalone"` is present in `frontend/next.config.ts`
- Rebuild cleanly: `docker compose build --no-cache frontend`

---

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review API docs at `/docs` endpoint

---

**Built with ❤️ for traders and investors**

