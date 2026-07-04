from fastapi import FastAPI, HTTPException

from app.models import ParseRequest, ParseResponse
from app.parser import parse

app = FastAPI(title="Bug Fixer AI Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse_file(req: ParseRequest):
    try:
        return parse(req.file_content, req.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
