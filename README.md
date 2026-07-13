# AI Bug Fixer

An AI-powered assistant that takes a bug report and a codebase, reasons through execution flow using AST parsing, semantic search, and multi-agent planning — then generates a root cause analysis and patch.

## Pipeline

```
Upload Repository → Parse Files → Build AST → Create Embeddings
       → Index Repository → Analyze Bug → Plan Investigation
       → Search Relevant Code → Reason Across Files
       → Generate RCA → Suggest Patch
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Spring Boot 3.5 (Java 21) |
| AI Service | Python 3.9+ (FastAPI + uvicorn) |
| Database | PostgreSQL 16 |
| Vector Store | Qdrant |

## Project Structure

```
bug-fixer/
├── backend/          # Spring Boot API (upload, indexing, status)
├── ai-service/       # Python AI service (AST parsing, embeddings, search)
└── docker-compose.yml
```

---

## Running with Docker Compose (recommended)

All services — Postgres, Qdrant, AI service, and backend — start together.

**1. Set your HuggingFace token:**

```bash
# ai-service/.env
HF_API_TOKEN=hf_your_token_here
```

**2. Start everything:**

```bash
colima start        # start Docker runtime (macOS)
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8080 |
| AI Service | http://localhost:8000 |
| Qdrant dashboard | http://localhost:6333/dashboard |
| pgAdmin | http://localhost:80 |

---

## Running Locally (development)

### Prerequisites

- Java 21
- Python 3.9+
- PostgreSQL (local)
- Docker / Colima (for Qdrant)

### Setup

**1. Create the database (once):**

```sql
CREATE USER bugfixer_admin WITH PASSWORD 'bugfixer';
CREATE DATABASE bugfixer OWNER bugfixer_admin;
```

**2. Start Qdrant:**

```bash
colima start
docker-compose up -d qdrant
```

**3. Start the AI service:**

```bash
cd ai-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**4. Start the backend:**

```bash
cd backend
./mvnw spring-boot:run
```

---

## API Flow

### Step 1 — Upload a repository

```
POST /api/projects/upload
Content-Type: multipart/form-data

name=my-project
file=<project.zip>
```

Response:
```json
{
  "projectId": "9f803ce0-39f8-4c7f-a6d9-1d44894ae3ea",
  "projectName": "my-project",
  "status": "UPLOADED",
  "fileCount": 0
}
```

### Step 2 — Poll indexing status

```
GET /api/projects/{projectId}/status
```

Response:
```json
{
  "projectId": "9f803ce0-...",
  "status": "INDEXED",
  "fileCount": 42
}
```

Status transitions:

```
UPLOADED → PARSING → EMBEDDING → INDEXED
                               ↘ FAILED
```

Poll until `status` is `INDEXED` before searching.

### Step 3 — Search relevant code

The `/search` endpoint uses **hybrid search**: BM25 keyword search fused with vector (embedding) search via Reciprocal Rank Fusion (RRF). This handles both exact Java identifier queries (`CouponService`, `placeOrder`) and semantic queries (`null check before save`).

```
POST http://localhost:8000/search
Content-Type: application/json

{
  "query": "NullPointerException in order processing",
  "project_id": "9f803ce0-39f8-4c7f-a6d9-1d44894ae3ea",
  "top_k": 5
}
```

**Optional filters:**

| Field | Type | Description |
|-------|------|-------------|
| `class_name` | `string` | Return only chunks from this class |
| `language` | `string` | Return only chunks of this language (e.g. `"java"`) |
| `file_path_prefix` | `string` | Return only chunks whose file path starts with this prefix |

Example with filters:
```json
{
  "query": "save order",
  "project_id": "9f803ce0-...",
  "top_k": 5,
  "class_name": "OrderService",
  "file_path_prefix": "src/main/java/com/example/service/"
}
```

Response:
```json
{
  "query": "NullPointerException in order processing",
  "project_id": "9f803ce0-...",
  "results": [
    {
      "score": 0.015748,
      "file_path": "src/main/java/com/example/OrderService.java",
      "chunk_type": "method",
      "class_name": "OrderService",
      "method_name": "processOrder",
      "content": "CLASS: OrderService\nMETHOD: processOrder\n...",
      "start_line": 45,
      "end_line": 72,
      "callees": ["validate", "repository.save"]
    }
  ]
}
```

> `score` is the RRF fusion score. Higher is better but not directly comparable to cosine similarity.

---

## AI Service — Internal Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/search` | Hybrid search (BM25 + vector, RRF-fused) |
| `POST` | `/index` | Parse + embed + upsert a single file into Qdrant |
| `POST` | `/parse` | Parse a Java file, return AST (class, methods, call graph) |
| `GET` | `/tools` | List the agent tool schemas (Grok/OpenAI function-calling format) |
| `POST` | `/tools/{tool_name}` | Invoke a single agent tool with a JSON body of its arguments |
| `GET` | `/health` | Liveness check |

`/index` and `/parse` are called internally by the Spring Boot backend. `/search` and `/tools/*` can be called directly for testing.

### /parse response shape

```json
{
  "file_path": "OrderService.java",
  "class_name": "OrderService",
  "imports": ["java.util.List"],
  "methods": [
    {
      "name": "placeOrder",
      "signature": "public OrderResponse placeOrder(OrderRequest request)",
      "return_type": "OrderResponse",
      "parameters": [{ "name": "request", "type": "OrderRequest" }],
      "annotations": ["@Transactional"],
      "callees": ["validate", "applyDiscount"],
      "start_line": 12,
      "end_line": 20
    }
  ],
  "call_graph": [
    { "caller": "placeOrder", "callees": ["validate", "applyDiscount"] }
  ]
}
```

---

## Agent Tool Library

The AI service exposes a set of **tools** — plain functions over the indexed data
(Qdrant payloads + the extracted files on disk) that the LLM agent calls to
investigate a bug. Each tool has a Grok/OpenAI-compatible JSON schema; they are
registered in [`tools/tool_registry.py`](ai-service/tools/tool_registry.py) and
invocable individually for testing via `POST /tools/{tool_name}`.

> Every tool takes `project_id` as its first argument — the indexed data is
> partitioned by project. File paths are relative to the project root (the same
> paths returned by `search_repository`).

| Tool | Arguments | Purpose |
|------|-----------|---------|
| `search_repository` | `project_id, query, top_k?, class_name?, language?, file_path_prefix?` | Hybrid search over all chunks; returns top matches with file/class/method |
| `find_callers` | `project_id, method, class_name?` | Methods that call `method` (upstream in the call graph) |
| `find_callees` | `project_id, method, class_name?` | The methods a given method calls (downstream) |
| `get_method_signature` | `project_id, class_name, method` | Full signature + annotations + file imports for a method |
| `read_file` | `project_id, path` | Raw file content from disk (full context beyond chunks) |
| `grep` | `project_id, pattern, path?, max_results?` | Regex search across files for exact strings the embedder misses |

`find_callers`'s `class_name` is a **soft hint** — call-site receivers are variable
names (e.g. `orderRepository.save`), not class names — so matching is primarily on
method name. `read_file` and `grep` are sandboxed to the project root; paths that
escape it (`../`) are rejected.

**List the schemas:**

```
GET http://localhost:8000/tools
```

**Invoke a tool:**

```
POST http://localhost:8000/tools/find_callees
Content-Type: application/json

{ "project_id": "9f803ce0-...", "class_name": "OrderService", "method": "placeOrder" }
```

Response:
```json
{
  "tool": "find_callees",
  "result": {
    "class_name": "OrderService",
    "method_name": "placeOrder",
    "file_path": "src/main/java/com/example/OrderService.java",
    "callees": ["validate", "applyDiscount"]
  }
}
```

Status codes: unknown tool → `404`; missing/invalid arguments → `400`; tool error → `500`.

> **Note:** `get_method_signature` reads `signature`/`imports` from the Qdrant
> payload, and `read_file`/`grep` read the extracted files at
> `/tmp/bug-fixer/{project_id}/`. Re-index a project (re-upload its zip) after
> upgrading so chunks carry these fields; the Docker setup mounts `/tmp/bug-fixer`
> into both the backend and the ai-service so paths line up.

---

## Backend API Reference

### Projects

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/projects/upload` | Upload a zipped codebase |
| `GET` | `/api/projects` | List all projects |
| `GET` | `/api/projects/{id}` | Get project details |
| `GET` | `/api/projects/{id}/status` | Poll indexing status |

---

## Database Schema

| Table | Description |
|-------|-------------|
| `projects` | Uploaded codebases and their indexing status |
| `files` | Individual source files with language and SHA-256 hash |
| `code_chunks` | AST-parsed code chunks with Qdrant vector IDs |
| `investigations` | Bug investigation sessions |
| `patches` | AI-generated patches per investigation |

---

## How Search Works

```
Query
  │
  ├─ embed_batch()  →  vector search in Qdrant  →  ranked list A
  │                    (cosine similarity, optional class/language filter)
  │
  └─ BM25 (in-memory, per-project cache)        →  ranked list B
     camelCase-aware tokenizer

  RRF fusion: score = Σ 1/(rank + 1 + 60)
       ↓
  Post-filter by file_path_prefix (optional)
       ↓
  Top-k results
```

The BM25 index is built lazily on first search per project and cached in memory. It is invalidated automatically whenever a new file is indexed.
