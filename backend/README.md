# RAG-Based Company FAQ Chatbot — Backend Documentation

A production-minded, modular backend for an enterprise FAQ Chatbot powered by **Django**, **Django REST Framework (DRF)**, **PostgreSQL**, and a **Retrieval-Augmented Generation (RAG)** pipeline.

---

## 1. Architecture & RAG Pipeline Overview

```
                               +-----------------------------+
                               |     React + Vite Frontend   |
                               +--------------+--------------+
                                              |
                                     HTTP API Requests
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
|                                    Django REST Framework                                |
|                                                                                         |
|  /api/v1/health/        /api/v1/faqs/          /api/v1/chat/       /api/v1/conversations/  |
|  (Health & DB Status)   (List, Search, Filter) (RAG Orchestrator)  (Session & Message DB)  |
+---------------------------------------------+-------------------------------------------+
                                              |
                                              v
                               +-----------------------------+
                               |        RAG Pipeline         |
                               +--------------+--------------+
                                              |
     +----------------------------------------+---------------------------------------+
     |                                        |                                       |
     v                                        v                                       v
+----+-------------------+       +------------+------------+       +------------------+----+
|  Query Vectorization   |       |   Vector Similarity     |       | Grounded Prompting    |
|  - EmbeddingService    | ----> |   - pgvector / Cosine   | ----> | - Prompt Injection    |
|  - Dimension: 1536     |       |   - Top-K Chunks        |       |   Resistance          |
|  - Models: OpenAI /    |       |   - Relevance Threshold |       | - Configurable LLM    |
|    Deterministic Mock  |       |   - Source Attribution  |       |   (OpenAI, Groq, Mock)|
+------------------------+       +------------+------------+       +-----------------------+
                                              |
                                              v
                               +-----------------------------+
                               |    PostgreSQL Database      |
                               |    - faqs_faq               |
                               |    - knowledge_base_chunk   |
                               |    - conversations_conv     |
                               +-----------------------------+
```

### RAG Workflow
1. **User Query Input**: Received at `POST /api/v1/chat/` and validated.
2. **Embedding Generation**: Query is converted into a numerical vector using the configured `EmbeddingService`.
3. **Vector Similarity Retrieval**: Searches stored FAQ and document chunks using cosine similarity.
4. **Context Sufficiency Check**: Validates if retrieved chunks exceed the similarity threshold (default `0.25`). If no relevant context is found, returns a safe fallback message without hallucinating.
5. **Prompt Injection Resistance**: The system prompt treats all retrieved documents as untrusted data and strictly instructs the LLM not to execute embedded instructions or invent company details.
6. **LLM Generation**: Generates grounded, helpful answers and formats source citations with relevance scores.
7. **Conversation Persistence**: Persists user and assistant messages to PostgreSQL with full ownership tracking.

---

## 2. Directory Structure

```
backend/
├── config/
│   ├── __init__.py
│   ├── settings.py           # Database, DRF, CORS, and RAG configuration
│   ├── urls.py               # Master versioned URL routing (/api/v1/)
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── __init__.py
│   ├── common/               # Health check, exception handlers, pagination
│   │   ├── views.py          # GET /api/v1/health/
│   │   ├── exceptions.py     # Custom error formatting without leaking stack traces
│   │   └── pagination.py     # StandardResultsSetPagination
│   ├── faqs/                 # FAQ management and searching
│   │   ├── models.py         # FAQ model with category, keywords, active status
│   │   ├── serializers.py    # DRF serializer with field validation
│   │   ├── views.py          # List, detail, categories, search endpoints
│   │   ├── admin.py          # Django Admin integration
│   │   ├── urls.py
│   │   └── management/
│   │       └── commands/
│   │           └── load_sample_faqs.py # Populates 15 Nexora FAQs & embeds them
│   ├── knowledge_base/       # Chunker, embeddings, vector search, ingestion
│   │   ├── models.py         # KnowledgeDocument & DocumentChunk
│   │   ├── services/
│   │   │   ├── chunker.py           # TextChunker with sentence boundary preservation
│   │   │   ├── embedding_service.py # EmbeddingService (OpenAI, Mock)
│   │   │   ├── vector_search.py     # VectorSearchService (pgvector / Cosine)
│   │   │   └── ingestion_service.py # Ingestion pipeline
│   │   ├── serializers.py
│   │   ├── views.py          # Document upload & chunk inspection
│   │   └── admin.py
│   ├── chatbot/              # Central RAG orchestrator & chat API
│   │   ├── services/
│   │   │   ├── llm_provider.py      # OpenAI, Groq, Mock LLM providers
│   │   │   └── rag_service.py       # RAG pipeline orchestration
│   │   ├── serializers.py    # Request validation for question/message
│   │   ├── views.py          # POST /api/v1/chat/
│   │   └── urls.py
│   └── conversations/        # Persistent conversation history
│       ├── models.py         # Conversation & Message models (UUID keys)
│       ├── serializers.py
│       ├── views.py          # List, retrieve, clear, delete conversations
│       └── urls.py
├── .env                      # Local environment configuration
├── .env.example              # Placeholder template (no secrets)
├── .gitignore
├── requirements.txt          # Python dependencies
└── manage.py
```

---

## 3. Prerequisites

- **Python**: Version 3.12 or 3.13 (Verified on Python 3.13.6 AMD64).
- **PostgreSQL**: Version 15+ (Verified on PostgreSQL 17.10 on port 5432).
- **Node.js & npm**: (For running the frontend, Node 18+).

---

## 4. PostgreSQL & pgvector Setup

### A. Database Verification
Ensure PostgreSQL is running. In Windows PowerShell:
```powershell
Get-Service *postgre*
```

Create the application database if not already present:
```powershell
$env:PGPASSWORD='your_postgres_password'
psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE faq_chatbot_db;"
```

### B. pgvector Extension Notes
The backend is designed with **dual-mode vector support**:
1. **With pgvector installed**: Set `USE_PGVECTOR=True` in `.env`. The database uses native vector columns and the pgvector `<=>` cosine distance index.
2. **Standard PostgreSQL (Default)**: If the native pgvector C-extension binary (`vector.dll` / `vector.control`) is not installed on the PostgreSQL server, set `USE_PGVECTOR=False`. Vector embeddings are stored as JSON float arrays in PostgreSQL and cosine similarities are calculated accurately with zero runtime errors.

To install pgvector on Windows PostgreSQL 17 (optional):
- Download pre-compiled pgvector binaries for PostgreSQL 17 from official releases or build via MSVC:
  `nmake /F Makefile.win` and `nmake /F Makefile.win install`.
- Then enable in PostgreSQL:
  `CREATE EXTENSION IF NOT EXISTS vector;`

---

## 5. Python Environment Setup & Installation

From `D:\Vicky\Task11\backend`:

```powershell
# 1. Create Python virtual environment
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
pip install -r requirements.txt
```

---

## 6. Environment Variables Configuration

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Edit `.env` with your settings:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | Secret key for cryptographic signing | `your-secret-key` |
| `DJANGO_DEBUG` | Enable debug mode in development | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `faq_chatbot_db` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL user password | `root` |
| `DB_HOST` | PostgreSQL host | `127.0.0.1` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `USE_PGVECTOR` | Enable pgvector database extension | `False` |
| `CORS_ALLOWED_ORIGINS`| Allowed frontend origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `EMBEDDING_PROVIDER` | `mock` (offline) or `openai` | `mock` |
| `EMBEDDING_MODEL` | Embedding model identifier | `text-embedding-3-small` |
| `EMBEDDING_API_KEY` | API Key for embedding model | `sk-...` |
| `EMBEDDING_DIMENSION`| Embedding vector dimension | `1536` |
| `LLM_PROVIDER` | `mock` (offline), `openai`, or `groq` | `mock` |
| `LLM_MODEL` | LLM model identifier | `gpt-4o-mini` |
| `LLM_API_KEY` | API Key for LLM provider | `sk-...` / `gsk_...` |
| `RAG_TOP_K` | Number of chunks to retrieve | `4` |
| `RAG_SIMILARITY_THRESHOLD` | Minimum relevance threshold | `0.25` |

---

## 7. Database Migrations & Seeding Sample FAQs

```powershell
# Apply Django and app migrations to PostgreSQL
.\.venv\Scripts\python.exe manage.py migrate

# Load all 15 official company FAQs and embed them into the vector knowledge base
.\.venv\Scripts\python.exe manage.py load_sample_faqs

# (Optional) Create Django Superuser for the admin portal
.\.venv\Scripts\python.exe manage.py createsuperuser
```

---

## 8. Running the Backend Server

Start the Django development server:
```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

The API will be live at `http://127.0.0.1:8000/api/v1/`.

---

## 9. API Endpoints Reference

### A. Health Endpoint
- **URL**: `GET /api/v1/health/`
- **Description**: Verifies that the server is online and tests live PostgreSQL database connectivity.
- **Example Response**:
```json
{
  "status": "healthy",
  "service": "company-faq-rag-backend",
  "database": "connected",
  "version": "1.0.0"
}
```

### B. FAQ Endpoints
- **List FAQs**: `GET /api/v1/faqs/?category=General+Information`
- **FAQ Detail**: `GET /api/v1/faqs/<id>/`
- **List Categories**: `GET /api/v1/faqs/categories/`
- **Search FAQs**: `GET /api/v1/faqs/search/?q=refund`
  - Searches across questions, answers, and keywords.

### C. Chatbot RAG Endpoint
- **URL**: `POST /api/v1/chat/`
- **Description**: Central endpoint for question answering.
- **Example Request**:
```json
{
  "question": "What are your standard business hours?",
  "conversation_id": null
}
```
- **Example Response**:
```json
{
  "status": "success",
  "answer": "Our corporate headquarters and customer care teams operate Monday through Friday, 8:00 AM to 8:00 PM Eastern Time (ET). Critical technical support services are monitored 24/7/365 for Enterprise tier clients.",
  "conversation_id": "bfb55d0a-8ae8-4f66-8b17-cbca0515a581",
  "sources": [
    {
      "faq_id": 2,
      "question": "What are your standard business hours?",
      "category": "General Information",
      "relevance_score": 0.6427
    }
  ],
  "matched": true,
  "category": "General Information",
  "timestamp": "2026-10-24T12:25:00.000000Z"
}
```

### D. Conversation History Endpoints
- **List Conversations**: `GET /api/v1/conversations/`
- **Retrieve Conversation**: `GET /api/v1/conversations/<uuid>/`
- **Clear Conversation**: `POST /api/v1/conversations/<uuid>/clear/`
- **Delete Conversation**: `DELETE /api/v1/conversations/<uuid>/`

---

## 10. Running Automated Tests

Run the full Django test suite (27 comprehensive unit and integration tests):
```powershell
.\.venv\Scripts\python.exe manage.py test
```

All tests execute against PostgreSQL and cover:
- Health check and DB connectivity.
- FAQ listing, detail, categories, filtering, and search.
- FAQ creation and deletion permissions.
- Text chunking (boundary preservation and overlap).
- Embedding services and vector similarity calculations.
- Vector retrieval and relevance ranking.
- RAG chat validation, conversation persistence, and unsupported fallback.
- Conversation listing, retrieval, clear, and deletion.

---

## 11. Frontend Integration

The React frontend has been connected to the Django backend:
1. `frontend/.env` defines `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
2. `frontend/src/services/api.js` provides centralized communication.
3. `ChatPage` sends queries to `POST /api/v1/chat/` with live streaming of assistant answers and source metadata.
4. `FAQPage` loads categories and FAQs dynamically from `/api/v1/faqs/` and `/api/v1/faqs/categories/`.
5. Existing frontend CSS architecture (`src/index.css`) is completely preserved.
