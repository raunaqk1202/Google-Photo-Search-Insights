# Google Photos AI Discovery Engine

An **AI-powered user discovery engine** that scrapes, processes, and analyzes real user feedback at scale to surface structured insights about photo retrieval failures under incomplete memory.

## 🏗️ Architecture

| Layer | Technology |
| --- | --- |
| **Backend** | Python 3.11+, FastAPI, Celery, Redis |
| **Data Processing** | Pandas, spaCy, Hugging Face Transformers |
| **Database** | PostgreSQL 16 |
| **Vector DB** | ChromaDB (dev) → Qdrant (prod) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **LLM** | Groq Cloud API (`llama-3.1-70b-versatile`) |
| **Frontend** | React.js 18, Vite, Recharts |
| **Deployment** | Railway (backend), Vercel (frontend) |

## 📁 Project Structure

```
├── backend/              # Python API + scrapers + pipeline
│   ├── api/              # FastAPI application
│   │   ├── main.py       # App entrypoint
│   │   ├── config.py     # Pydantic settings
│   │   ├── database.py   # SQLAlchemy engine
│   │   ├── routers/      # API endpoints
│   │   ├── models/       # ORM + Pydantic models
│   │   └── services/     # Business logic
│   ├── scrapers/         # Data acquisition (Phase 1)
│   ├── pipeline/         # Data processing (Phase 2)
│   ├── alembic/          # Database migrations
│   └── tests/            # Backend tests
├── frontend/             # React.js SPA
├── docker/               # Docker Compose
├── docs/                 # Documentation
│   ├── problem Statement.md
│   ├── Architecture.md
│   ├── implementationPlan.md
│   └── edgeCase.md
└── scripts/              # Utilities (seed_db, etc.)
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local frontend development)

### 1. Clone & Configure

```bash
cp .env.example .env
# Edit .env with your API keys (Groq, Reddit, YouTube)
```

### 2. Start with Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts:
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **ChromaDB** (port 8000)
- **FastAPI Backend** (port 8080)
- **Celery Worker** (background)
- **Celery Beat** (scheduler)
- **React Frontend** (port 5173)

### 3. Verify

```bash
# Health check
curl http://localhost:8080/api/v1/health

# API docs
open http://localhost:8080/docs

# Frontend
open http://localhost:5173
```

### 4. Seed Database

```bash
# From the project root
python scripts/seed_db.py
```

## 🛠️ Local Development (without Docker)

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm test
```

## 📖 Documentation

| Document | Description |
| --- | --- |
| [Problem Statement](docs/problem%20Statement.md) | Product context and research questions |
| [Architecture](docs/Architecture.md) | System design, data model, API contract |
| [Implementation Plan](docs/implementationPlan.md) | Phased build plan with acceptance criteria |
| [Edge Cases](docs/edgeCase.md) | 100+ edge cases with handling strategies |

## 📡 API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/chat` | Conversational query (RAG pipeline) |
| `GET` | `/api/v1/citations/{id}` | Citation detail drill-down |
| `POST` | `/api/v1/scrape/trigger` | Trigger scrape job |
| `GET` | `/api/v1/scrape/status` | Scrape job status |
| `GET` | `/api/v1/data/reviews` | Browse structured reviews |
| `GET` | `/api/v1/analytics/*` | Pre-computed analytics |

## 🚀 Production Deployment (Railway & Vercel)

This project is configured for split deployment: the backend on **Railway** and the frontend on **Vercel**.

### Backend (Railway)
1. Link your GitHub repository to a new Railway project.
2. Railway will automatically detect the services from `docker/docker-compose.prod.yml` or the `Dockerfile` in `/backend`.
3. Provision **PostgreSQL** and **Redis** plugins via the Railway dashboard.
4. Set the following environment variables:
   - `DATABASE_URL` (auto-populated by Railway Postgres)
   - `REDIS_URL` (auto-populated by Railway Redis)
   - `APP_ENV=production`
   - `CORS_ORIGINS=https://your-vercel-app-url.vercel.app`
   - `GROQ_API_KEY`, `REDDIT_CLIENT_ID`, `YOUTUBE_API_KEY`, etc.
5. Deploy the backend services (`FastAPI`, `Celery Worker`, `Celery Beat`).

### Frontend (Vercel)
1. Import the project into Vercel, setting the **Framework Preset** to Vite.
2. Set the Root Directory to `frontend`.
3. Add the following environment variable:
   - `VITE_API_BASE_URL=https://your-railway-backend-url.up.railway.app`
4. Deploy. Vercel will build the React SPA and distribute it via their edge network.

## 📝 License

Internal tool — Google Photos Core Experience team.
