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
| AI Service | Python (FastAPI) |
| Database | PostgreSQL |
| Vector Store | Qdrant |

## Project Structure

```
bug-fixer/
├── backend/          # Spring Boot API
├── ai-service/       # Python AI service (AST parsing, embeddings, agents)
└── docker-compose.yml
```

## Prerequisites

- Java 21
- PostgreSQL (local)
- Docker (for Qdrant)

## Setup

**1. Create the database (once):**
```sql
CREATE USER bugfixer_admin WITH PASSWORD 'bugfixer';
CREATE DATABASE bugfixer OWNER bugfixer_admin;
```

**2. Start Qdrant:**
```bash
docker-compose up -d
```

**3. Run the backend:**
```bash
cd backend
./mvnw spring-boot:run
```

The API starts on `http://localhost:8080`.

## API Endpoints

### Projects

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/projects/upload` | Upload a zipped codebase |
| `GET` | `/api/projects` | List all projects |
| `GET` | `/api/projects/{id}` | Get project details |
| `GET` | `/api/projects/{id}/status` | Poll indexing status |

### Upload a project (Postman)

`POST /api/projects/upload` — Body → form-data:
- `name` (text) — project name
- `file` (file) — `.zip` of the codebase

### Project Status Flow

```
UPLOADED → PARSING → INDEXED
                   ↘ FAILED
```

Poll `GET /api/projects/{id}/status` until status is `INDEXED` or `FAILED`.

## Database Schema

| Table | Description |
|-------|-------------|
| `projects` | Uploaded codebases and their indexing status |
| `files` | Individual source files with language and SHA-256 hash |
| `code_chunks` | AST-parsed code chunks with Qdrant vector IDs |
| `investigations` | Bug investigation sessions |
| `patches` | AI-generated patches per investigation |
