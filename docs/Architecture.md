# Architecture: Google Photos AI Discovery Engine

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [System Context Diagram](#2-system-context-diagram)
3. [High-Level Component Architecture](#3-high-level-component-architecture)
4. [Tier 1 — Python API Backend](#4-tier-1--python-api-backend)
5. [Tier 2 — Groq-Powered RAG Pipeline](#5-tier-2--groq-powered-rag-pipeline)
6. [Tier 3 — React.js Frontend](#6-tier-3--reactjs-frontend)
7. [Data Flow](#7-data-flow)
8. [Data Model & Schema Design](#8-data-model--schema-design)
9. [Vector Database Design](#9-vector-database-design)
10. [API Contract](#10-api-contract)
11. [Infrastructure & Deployment](#11-infrastructure--deployment)
12. [Security & Compliance](#12-security--compliance)
13. [Key Design Decisions](#13-key-design-decisions)

---

## 1. Architecture Overview

The system is a **three-tier, decoupled web application** designed to function as a PM-facing discovery engine. It autonomously scrapes, processes, and analyzes real user feedback from public sources to surface structured insights about photo retrieval failures under incomplete memory.

### Guiding Principles

| Principle | Rationale |
| --- | --- |
| **Live data only** | No mock or synthetic data. Every insight must trace back to a real user statement. |
| **Evidence-first analysis** | Raw text is rigorously structured (Pandas DataFrames) before reaching the LLM. |
| **Ultra-low latency inference** | Groq hardware acceleration ensures conversational-speed responses. |
| **Full citation traceability** | Every answer in the UI links back to the original scraped review/comment. |
| **Decoupled tiers** | Backend, RAG pipeline, and frontend are independently deployable services. |

---

## 2. System Context Diagram

```mermaid
C4Context
    title System Context — AI Discovery Engine

    Person(pm, "Product Manager", "Asks investigative questions via conversational UI")

    System(engine, "AI Discovery Engine", "Scrapes, structures, and analyzes user feedback for photo-retrieval insights")

    System_Ext(playstore, "Google Play Store")
    System_Ext(appstore, "Apple App Store")
    System_Ext(reddit, "Reddit")
    System_Ext(community, "Google Photos Community Forums")
    System_Ext(youtube, "YouTube Comments")

    Rel(pm, engine, "Queries insights", "HTTPS / WebSocket")
    Rel(engine, playstore, "Scrapes reviews")
    Rel(engine, appstore, "Scrapes reviews")
    Rel(engine, reddit, "Scrapes discussions")
    Rel(engine, community, "Scrapes support threads")
    Rel(engine, youtube, "Scrapes comments")
```

---

## 3. High-Level Component Architecture

```mermaid
graph TB
    subgraph "Tier 3 — React.js Frontend"
        UI["Conversational Chat UI"]
        Citations["Citation Explorer Panel"]
        Dashboard["Insight Dashboard"]
    end

    subgraph "Tier 2 — RAG Pipeline"
        Retriever["Vector Retriever"]
        Reranker["Cross-Encoder Reranker"]
        GroqLLM["Groq LLM — UX Researcher Persona"]
        PromptEngine["Prompt Engineering Layer"]
    end

    subgraph "Tier 1 — Python API Backend"
        API["FastAPI Application"]
        Scraper["Scraping Engine"]
        Cleaner["Data Cleaning Pipeline"]
        Structurer["Structuring & Feature Extraction"]
        Embedder["Embedding Service"]
        Scheduler["Job Scheduler"]
    end

    subgraph "Data Stores"
        VectorDB["Vector Database — ChromaDB / Qdrant"]
        RelationalDB["PostgreSQL — Structured Data"]
        Cache["Redis — Response Cache"]
    end

    UI --> API
    Citations --> API
    Dashboard --> API
    API --> Retriever
    Retriever --> VectorDB
    Retriever --> Reranker
    Reranker --> PromptEngine
    PromptEngine --> GroqLLM
    Scraper --> Cleaner
    Cleaner --> Structurer
    Structurer --> Embedder
    Embedder --> VectorDB
    Structurer --> RelationalDB
    Scheduler --> Scraper
    API --> Cache
```

---

## 4. Tier 1 — Python API Backend

### 4.1 Responsibilities

* Scrape live user feedback from all target sources
* Clean, deduplicate, and validate raw text
* Structure unstructured text into Pandas DataFrames with extracted features
* Generate embeddings and manage the vector database
* Expose REST API endpoints for the frontend and RAG pipeline
* Schedule periodic re-scraping jobs

### 4.2 Scraping Engine

| Source | Method | Rate Limiting Strategy |
| --- | --- | --- |
| Google Play Store | `google-play-scraper` | Exponential backoff, rotating proxies |
| Apple App Store | `app-store-scraper` | Throttled requests with jitter |
| Reddit | Reddit API (PRAW) / Async PRAW | OAuth2 rate-limited client |
| Google Photos Community | HTTP scraper (BeautifulSoup / Playwright) | Polite crawl with `robots.txt` compliance |
| YouTube Comments | YouTube Data API v3 | Quota-managed batch requests |

#### Scraper Module Structure

```
backend/
├── scrapers/
│   ├── base_scraper.py          # Abstract base class
│   ├── playstore_scraper.py
│   ├── appstore_scraper.py
│   ├── reddit_scraper.py
│   ├── community_scraper.py
│   └── youtube_scraper.py
├── pipeline/
│   ├── cleaner.py               # Deduplication, spam removal, language filter
│   ├── structurer.py            # Feature extraction into DataFrames
│   ├── embedder.py              # Embedding generation (sentence-transformers)
│   └── relevance_classifier.py  # Retrieval-relevance binary classifier
```

### 4.3 Data Cleaning Pipeline

```mermaid
graph LR
    A["Raw Scraped Text"] --> B["Language Detection"]
    B --> C["Deduplication — MinHash LSH"]
    C --> D["Spam / Bot Removal"]
    D --> E["Retrieval-Relevance Classifier"]
    E --> F["Structured DataFrame"]
```

**Cleaning steps:**

1. **Language detection** — Retain English-language content (extensible to other languages).
2. **Deduplication** — MinHash Locality-Sensitive Hashing to detect near-duplicate reviews across sources.
3. **Spam / bot removal** — Heuristic + ML classifier to filter review-farm content.
4. **Retrieval-relevance classification** — Binary classifier (fine-tuned or zero-shot) to identify whether a review relates to *retrieving an existing photo under incomplete memory*, filtering out general feature requests, upload issues, storage complaints, etc.

### 4.4 Structuring & Feature Extraction

Every relevant review is parsed into a structured record with the following extracted fields:

| Field | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Unique identifier |
| `source` | `enum` | Platform of origin |
| `source_url` | `string` | Original URL for citation |
| `scraped_at` | `datetime` | Timestamp of scrape |
| `original_text` | `string` | Verbatim user statement |
| `cleaned_text` | `string` | Preprocessed text |
| `language` | `string` | Detected language |
| `sentiment_score` | `float` | Compound sentiment (-1 to 1) |
| `memory_cues` | `list[string]` | What the user remembers (person, place, event, object, etc.) |
| `forgotten_attributes` | `list[string]` | What the user has forgotten (date, location, album, etc.) |
| `search_behavior` | `list[string]` | How the user attempted retrieval |
| `failure_mode` | `string` | Where retrieval broke down |
| `outcome` | `enum` | `retrieved` / `partial` / `abandoned` / `unknown` |
| `photo_category` | `string` | Type of photo being sought |
| `user_effort_signal` | `string` | Indicators of frustration / repeated attempts |
| `retrieval_archetype` | `string` | Classified memory-retrieval pattern |

This extraction is performed using a combination of:

* **Rule-based NLP** (spaCy NER, regex patterns)
* **Zero-shot classification** (Hugging Face `transformers`)
* **LLM-assisted extraction** (Groq for batch labeling with human-in-the-loop validation)

### 4.5 FastAPI Application

```
backend/
├── api/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── routers/
│   │   ├── scrape.py            # Trigger & monitor scrape jobs
│   │   ├── data.py              # Browse structured datasets
│   │   ├── chat.py              # Conversational query endpoint
│   │   ├── citations.py         # Drill-down citation explorer
│   │   └── health.py            # Health check
│   ├── models/
│   │   ├── review.py            # Pydantic models for structured reviews
│   │   ├── query.py             # Chat query / response models
│   │   └── citation.py          # Citation reference models
│   ├── services/
│   │   ├── rag_service.py       # Orchestrates the RAG pipeline
│   │   ├── scrape_service.py    # Manages scraping lifecycle
│   │   └── analytics_service.py # Pre-computed analytics queries
│   └── config.py                # Environment & API key management
```

---

## 5. Tier 2 — Groq-Powered RAG Pipeline

### 5.1 Responsibilities

* Retrieve the most relevant structured review chunks from the vector database
* Re-rank results for contextual precision
* Synthesize evidence-backed, cited answers as a UX Researcher persona
* Maintain ultra-low latency (target < 2s end-to-end)

### 5.2 Pipeline Flow

```mermaid
sequenceDiagram
    participant PM as Product Manager
    participant API as FastAPI Backend
    participant VDB as Vector Database
    participant RR as Cross-Encoder Reranker
    participant PE as Prompt Engine
    participant Groq as Groq LLM

    PM->>API: Ask investigative question
    API->>VDB: Semantic search (top-k=50)
    VDB-->>API: Candidate chunks with metadata
    API->>RR: Re-rank candidates (top-k=15)
    RR-->>API: Re-ranked chunks
    API->>PE: Build prompt with context + system persona
    PE->>Groq: Send prompt (streaming)
    Groq-->>PE: Stream tokens
    PE-->>API: Structured response with citations
    API-->>PM: Rendered answer + citation links
```

### 5.3 Retrieval Strategy

| Stage | Component | Details |
| --- | --- | --- |
| **Embedding** | `sentence-transformers/all-MiniLM-L6-v2` (or `BGE-large`) | Generates 384/1024-dim embeddings for each structured review chunk |
| **Vector search** | ChromaDB or Qdrant | Approximate nearest-neighbor search, top-k=50 |
| **Re-ranking** | Cross-encoder (e.g., `ms-marco-MiniLM-L-6-v2`) | Reduces to top-k=15 most contextually relevant chunks |
| **Metadata filtering** | Pre-filter by source, date range, photo category, failure mode | Enables scoped queries like "show me Reddit complaints about travel photo retrieval" |

### 5.4 Prompt Engineering — UX Researcher Persona

The system prompt configures the Groq LLM as a **senior UX researcher** with the following behavior:

* Answers are grounded exclusively in the retrieved evidence
* Every claim includes inline citations referencing `[source_id]`
* Distinguishes between *direct user evidence*, *inferred patterns*, and *hypotheses*
* Quantifies where sample size supports it; labels qualitative signals as "directional"
* Does not fabricate prevalence or overgeneralize from small samples
* Structures responses around: Problem → Evidence → Frequency → Failure Mode → Opportunity

### 5.5 Groq Configuration

| Parameter | Value | Rationale |
| --- | --- | --- |
| Model | `llama-3.1-70b-versatile` (or latest available) | Best balance of reasoning and speed on Groq |
| Temperature | `0.2` | Low creativity — prioritize factual grounding |
| Max tokens | `4096` | Sufficient for detailed, cited responses |
| Streaming | `enabled` | Real-time token delivery to frontend |

---

## 6. Tier 3 — React.js Frontend

### 6.1 Responsibilities

* Provide a conversational chat interface for PM queries
* Render structured, cited responses with drill-down capability
* Display pre-computed dashboards (opportunity matrix, memory cue maps, failure modes)
* Enable citation exploration: Opportunity → Problem → Review → Original Source

### 6.2 Component Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWindow.jsx        # Main conversational interface
│   │   │   ├── MessageBubble.jsx      # Individual message rendering
│   │   │   ├── CitationTag.jsx        # Inline citation chip
│   │   │   └── SuggestedQuestions.jsx  # Pre-seeded investigative prompts
│   │   ├── Citations/
│   │   │   ├── CitationPanel.jsx      # Side panel for drilling into sources
│   │   │   ├── ReviewCard.jsx         # Individual review with metadata
│   │   │   └── SourceBadge.jsx        # Platform icon + link
│   │   ├── Dashboard/
│   │   │   ├── OpportunityMatrix.jsx  # Comparison table (Section 10 of problem stmt)
│   │   │   ├── MemoryCueMap.jsx       # Visual: remembered vs. forgotten attributes
│   │   │   ├── FailureModeChart.jsx   # Breakdown of retrieval failure points
│   │   │   └── ArchetypeCards.jsx     # Retrieval archetype profiles
│   │   └── Layout/
│   │       ├── Sidebar.jsx
│   │       ├── Header.jsx
│   │       └── MainLayout.jsx
│   ├── hooks/
│   │   ├── useChat.js                 # Chat state management + streaming
│   │   ├── useCitations.js            # Citation drill-down logic
│   │   └── useAnalytics.js            # Dashboard data fetching
│   ├── services/
│   │   └── api.js                     # Axios/fetch wrapper for backend API
│   ├── App.jsx
│   └── index.jsx
```

### 6.3 Key UI Features

| Feature | Description |
| --- | --- |
| **Conversational Chat** | Streaming responses rendered in real-time; markdown support for tables, lists, bold emphasis |
| **Inline Citations** | Clickable `[1]`, `[2]` tags within answers that expand to show the original review |
| **Citation Explorer** | Side panel: click a citation → see full review text, source URL, platform, date, extracted metadata |
| **Suggested Questions** | Pre-seeded with the four key investigative questions from the problem statement |
| **Opportunity Matrix** | Interactive table comparing opportunity areas across frequency, severity, evidence strength |
| **Memory Cue Map** | Visual chart: what users remember vs. what they forget, by photo category |
| **Failure Mode Breakdown** | Bar/treemap chart of retrieval failure points |

### 6.4 Streaming & Real-Time

* **Server-Sent Events (SSE)** or **WebSocket** connection for streaming LLM responses
* Frontend renders tokens incrementally as they arrive from Groq
* Citation metadata is delivered in a structured JSON payload appended after the streamed text

---

## 7. Data Flow

### 7.1 Ingestion Flow (Batch)

```mermaid
graph LR
    A["Scheduled Job — Cron / Celery Beat"] --> B["Scraping Engine"]
    B --> C["Raw Reviews Store — PostgreSQL"]
    C --> D["Cleaning Pipeline"]
    D --> E["Structured DataFrame"]
    E --> F["Feature Extraction — NLP + LLM"]
    F --> G["PostgreSQL — Structured Records"]
    F --> H["Embedding Generation"]
    H --> I["Vector Database — ChromaDB/Qdrant"]
```

### 7.2 Query Flow (Real-Time)

```mermaid
graph LR
    A["PM asks question in React UI"] --> B["FastAPI /chat endpoint"]
    B --> C["Query embedding"]
    C --> D["Vector search — top 50"]
    D --> E["Cross-encoder re-rank — top 15"]
    E --> F["Prompt assembly + system persona"]
    F --> G["Groq LLM — streaming"]
    G --> H["Streamed response + citation JSON"]
    H --> I["React UI renders answer + citations"]
```

---

## 8. Data Model & Schema Design

### 8.1 Core Tables (PostgreSQL)

```mermaid
erDiagram
    SCRAPE_JOB ||--o{ RAW_REVIEW : produces
    RAW_REVIEW ||--o| STRUCTURED_REVIEW : "cleaned into"
    STRUCTURED_REVIEW }o--o{ MEMORY_CUE : has
    STRUCTURED_REVIEW }o--o| FAILURE_MODE : "classified as"
    STRUCTURED_REVIEW }o--o| RETRIEVAL_ARCHETYPE : "belongs to"

    SCRAPE_JOB {
        uuid id PK
        string source
        datetime started_at
        datetime completed_at
        int total_collected
        string status
    }

    RAW_REVIEW {
        uuid id PK
        uuid scrape_job_id FK
        string source
        string source_url
        text original_text
        datetime published_at
        datetime scraped_at
        float rating
        string author_handle
    }

    STRUCTURED_REVIEW {
        uuid id PK
        uuid raw_review_id FK
        text cleaned_text
        string source
        string source_url
        string language
        float sentiment_score
        string photo_category
        string outcome
        string user_effort_signal
        string retrieval_archetype_id FK
        string failure_mode_id FK
        boolean is_retrieval_relevant
    }

    MEMORY_CUE {
        uuid id PK
        uuid structured_review_id FK
        string cue_type
        string cue_value
        string retention_level
    }

    FAILURE_MODE {
        uuid id PK
        string name
        string description
    }

    RETRIEVAL_ARCHETYPE {
        uuid id PK
        string name
        string description
    }
```

---

## 9. Vector Database Design

### 9.1 Collection Schema

| Field | Type | Description |
| --- | --- | --- |
| `id` | `string` | Maps to `structured_review.id` |
| `embedding` | `float[384]` | Sentence-transformer embedding |
| `text` | `string` | Cleaned review text (chunked if > 512 tokens) |
| `source` | `string` | Platform metadata for filtering |
| `photo_category` | `string` | Metadata filter |
| `failure_mode` | `string` | Metadata filter |
| `retrieval_archetype` | `string` | Metadata filter |
| `outcome` | `string` | Metadata filter |
| `source_url` | `string` | For citation linking |
| `published_at` | `string` | Date filter |

### 9.2 Indexing Strategy

* **Chunking**: Reviews > 512 tokens are split with 50-token overlap using a sentence-aware splitter
* **Index type**: HNSW (Hierarchical Navigable Small World) for sub-millisecond ANN search
* **Distance metric**: Cosine similarity
* **Metadata filters**: Applied pre-retrieval to scope searches by source, category, failure mode

---

## 10. API Contract

### 10.1 Core Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/chat` | Submit a conversational query; returns streamed response |
| `GET` | `/api/v1/citations/{id}` | Retrieve full citation details for a referenced review |
| `GET` | `/api/v1/analytics/opportunities` | Pre-computed opportunity comparison matrix |
| `GET` | `/api/v1/analytics/memory-cues` | Aggregated memory cue frequency data |
| `GET` | `/api/v1/analytics/failure-modes` | Failure mode distribution |
| `GET` | `/api/v1/analytics/archetypes` | Retrieval archetype profiles |
| `POST` | `/api/v1/scrape/trigger` | Manually trigger a scrape job |
| `GET` | `/api/v1/scrape/status` | Check scrape job status |
| `GET` | `/api/v1/data/reviews` | Paginated browse of structured reviews |
| `GET` | `/api/v1/health` | Health check |

### 10.2 Chat Request / Response

**Request:**
```json
{
  "query": "What types of old photos are most difficult to retrieve?",
  "filters": {
    "sources": ["reddit", "playstore"],
    "date_range": { "from": "2024-01-01", "to": "2025-09-01" }
  },
  "session_id": "uuid"
}
```

**Response (streamed via SSE):**
```json
{
  "answer": "Based on analysis of 1,247 relevant reviews, travel photos are the most frequently cited category...[1][2]",
  "citations": [
    {
      "id": "c-001",
      "ref_number": 1,
      "text": "I can never find my vacation photos from last year...",
      "source": "reddit",
      "source_url": "https://reddit.com/r/googlephotos/...",
      "published_at": "2025-03-14",
      "photo_category": "travel",
      "failure_mode": "temporal_uncertainty"
    }
  ],
  "confidence": "moderate",
  "evidence_type": "pattern",
  "sample_size": 1247
}
```

---

## 11. Infrastructure & Deployment

### 11.1 Deployment Topology

```mermaid
graph TB
    subgraph "Client"
        Browser["React.js SPA — Vercel / Netlify"]
    end

    subgraph "Application Layer"
        FastAPI["FastAPI Backend — Docker Container"]
        Celery["Celery Workers — Scraping & Processing"]
    end

    subgraph "AI Layer"
        GroqAPI["Groq Cloud API"]
        HF["Hugging Face Models — Embeddings + Reranker"]
    end

    subgraph "Data Layer"
        PG["PostgreSQL"]
        Qdrant["Qdrant / ChromaDB"]
        Redis["Redis — Cache + Message Broker"]
    end

    Browser --> FastAPI
    FastAPI --> GroqAPI
    FastAPI --> HF
    FastAPI --> PG
    FastAPI --> Qdrant
    FastAPI --> Redis
    Celery --> PG
    Celery --> Qdrant
    Celery --> Redis
```

### 11.2 Technology Choices

| Layer | Technology | Rationale |
| --- | --- | --- |
| API Framework | FastAPI | Async-native, OpenAPI auto-docs, Pydantic validation |
| Task Queue | Celery + Redis | Distributed scraping jobs with retries and scheduling |
| Scheduler | Celery Beat | Periodic re-scraping (configurable: daily/weekly) |
| Database | PostgreSQL | Structured review storage, analytics queries, ACID compliance |
| Vector DB | ChromaDB (dev) / Qdrant (prod) | ChromaDB for rapid prototyping; Qdrant for production scale + filtering |
| Embeddings | `sentence-transformers` | Local inference; no API dependency for embeddings |
| Reranker | `cross-encoder` | Local inference; improves retrieval precision |
| LLM | Groq Cloud API | Ultra-low latency inference; hardware-accelerated |
| Frontend | React.js + Vite | Fast build tooling, component ecosystem |
| Deployment | Docker Compose (dev) / Kubernetes (prod) | Containerized, reproducible environments |
| CI/CD | GitHub Actions | Automated testing, linting, deployment |

### 11.3 Environment Configuration

```
# .env (example)
GROQ_API_KEY=gsk_...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
YOUTUBE_API_KEY=...
POSTGRES_URL=postgresql://user:pass@localhost:5432/discovery
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

---

## 12. Security & Compliance

| Concern | Mitigation |
| --- | --- |
| **API keys** | Stored in environment variables; never committed to version control |
| **Scraped data** | Only publicly available content; no PII extraction; compliance with platform ToS |
| **Rate limiting** | Backend enforces per-source rate limits; respects `robots.txt` |
| **Authentication** | Frontend protected by session-based or JWT auth (internal tool) |
| **Data retention** | Configurable TTL on scraped data; option to purge on demand |
| **CORS** | Strict origin allowlisting on FastAPI |
| **Input sanitization** | Pydantic models validate all API inputs; parameterized DB queries |

---

## 13. Key Design Decisions

| Decision | Choice | Alternatives Considered | Rationale |
| --- | --- | --- | --- |
| LLM inference provider | **Groq** | OpenAI, Anthropic, local Ollama | Ultra-low latency is a core requirement; Groq's LPU architecture delivers fastest token throughput |
| Vector DB | **ChromaDB → Qdrant** | Pinecone, Weaviate, Milvus | ChromaDB for zero-config dev; Qdrant for production metadata filtering + horizontal scaling |
| Embedding model | **sentence-transformers (local)** | OpenAI embeddings API | Eliminates external dependency for embeddings; lower cost at scale; full control |
| Data processing | **Pandas DataFrames** | Spark, Polars | Explicitly required by problem statement; sufficient for expected data volumes (tens of thousands of reviews) |
| API framework | **FastAPI** | Flask, Django | Native async support for streaming SSE; auto-generated OpenAPI docs; Pydantic-first |
| Frontend framework | **React.js** | Next.js, Vue, Svelte | Explicitly required by problem statement; rich ecosystem for chat interfaces |
| Task orchestration | **Celery** | APScheduler, Airflow | Battle-tested for distributed scraping tasks; native retry/backoff; Celery Beat for scheduling |
| Streaming protocol | **SSE (Server-Sent Events)** | WebSocket, polling | Simpler than WebSocket for unidirectional streaming; native browser support; sufficient for chat UX |

---

> **Next Steps**: See [problem Statement.md](file:///Users/raunaqkaicker/Documents/Google%20photos%20AI%20discovery%20engine/docs/problem%20Statement.md) for the full problem context driving this architecture.
