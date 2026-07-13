from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import Body, FastAPI, HTTPException

from app.bm25_index import invalidate as invalidate_bm25
from app.chunking import produce_chunks
from app.embedding import embed_batch
from app.models import IndexRequest, IndexResponse, ChunkResult, ParseRequest, ParseResponse, SearchRequest, SearchResponse, SearchHit
from app.parser import parse
from app.qdrant_store import ensure_collection, upsert_chunks
from app.search_service import hybrid_search
from tools.tool_registry import TOOL_SCHEMAS, dispatch


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    yield


app = FastAPI(title="Bug Fixer AI Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tools")
def list_tools():
    """Return the Grok/OpenAI-compatible schemas for every registered tool."""
    return {"tools": TOOL_SCHEMAS}


@app.post("/tools/{tool_name}")
def invoke_tool(tool_name: str, body: dict = Body(default={})):
    """Manually invoke a tool by name with a JSON body of its keyword arguments."""
    try:
        return {"tool": tool_name, "result": dispatch(tool_name, body)}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
def search_code(req: SearchRequest):
    fused = hybrid_search(
        project_id=req.project_id,
        query=req.query,
        top_k=req.top_k,
        class_name=req.class_name,
        language=req.language,
        file_path_prefix=req.file_path_prefix,
    )

    results = [
        SearchHit(
            score=round(h["rrf_score"], 6),
            file_path=h.get("file_path", ""),
            chunk_type=h.get("chunk_type", ""),
            class_name=h.get("class_name"),
            method_name=h.get("method_name"),
            content=h.get("content", ""),
            start_line=h.get("start_line", 0),
            end_line=h.get("end_line", 0),
            callees=h.get("callees", []),
        )
        for h in fused
    ]
    return SearchResponse(query=req.query, project_id=req.project_id, results=results)


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

        # 6. Invalidate cached BM25 index so next search includes this file
        invalidate_bm25(req.project_id)

        return IndexResponse(
            file_path=req.file_path,
            project_id=req.project_id,
            file_id=req.file_id,
            chunks=chunk_results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
