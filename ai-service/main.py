from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException

from app.chunking import produce_chunks
from app.embedding import embed_batch
from app.models import IndexRequest, IndexResponse, ChunkResult, ParseRequest, ParseResponse
from app.parser import parse
from app.qdrant_store import ensure_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    yield


app = FastAPI(title="Bug Fixer AI Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse_file(req: ParseRequest):
    try:
        return parse(req.file_content, req.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResponse)
def index_file(req: IndexRequest):
    try:
        print(f"Indexing file: {req.file_path} (project_id={req.project_id}, file_id={req.file_id})")
        from app.qdrant_store import upsert_chunks

        # 1. Parse → AST
        parse_result = parse(req.file_content, req.file_path)

        # 2. Chunk — one per method + one class-level chunk
        raw_chunks = produce_chunks(parse_result, req.file_content, req.file_path)
        if not raw_chunks:
            return IndexResponse(
                file_path=req.file_path,
                project_id=req.project_id,
                file_id=req.file_id,
                chunks=[],
            )

        # 3. Embed all chunk contents in one batched call
        texts = [c.content for c in raw_chunks]
        vectors = embed_batch(texts)

        # 4. Upsert to Qdrant, get back point IDs
        point_ids = upsert_chunks(
            chunks=raw_chunks,
            vectors=vectors,
            project_id=req.project_id,
            file_id=req.file_id,
            file_path=req.file_path,
            language=req.language,
        )

        # 5. Build response so Java can store qdrant_point_id in Postgres
        chunk_results = [
            ChunkResult(
                chunk_type=chunk.chunk_type,
                method_name=chunk.method_name,
                class_name=chunk.class_name,
                content=chunk.content,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                annotations=chunk.annotations,
                callees=chunk.callees,
                qdrant_point_id=pid,
            )
            for chunk, pid in zip(raw_chunks, point_ids)
        ]

        return IndexResponse(
            file_path=req.file_path,
            project_id=req.project_id,
            file_id=req.file_id,
            chunks=chunk_results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
