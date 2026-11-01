"""
REST API used by the React frontend.

Run : uvicorn api:app --reload --port 8000
If frontend/dist exists (npm run build), the frontend is also served on http://localhost:8000
"""

import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import tools
from agent import ask_agent
from chat import cv_graph

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
FILE_NAME_PATTERN = re.compile(r"^[\w-]+\.pdf$")

app = FastAPI(title="CV Screening Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    mode: Literal["agent", "rag"] = "agent"
    history: list[ChatMessage] = []


def sort_cited_first(answer, sources):
    for source in sources:
        source["cited"] = f"[{source['file_name']}]" in answer
    return sorted(sources, key=lambda source: not source["cited"])


@app.get("/api/health")
def health():
    try:
        count = tools.client.count(tools.COLLECTION_NAME, exact=True).count
    except Exception as e:
        raise HTTPException(503, f"Qdrant is not reachable: {e}")
    return {"status": "ok", "cv_count": count}


@app.get("/api/categories")
def categories():
    return tools.category_counts()


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        if request.mode == "agent":
            history = [message.model_dump() for message in request.history]
            result = ask_agent(request.question, history)
            filters = None
        else:
            # the RAG pipeline has no memory, it only uses the question
            state = cv_graph.invoke({"question": request.question})
            result = {"answer": state["answer"], "sources": state["sources"], "tool_calls": []}
            filters = state["filters"].model_dump()
    except Exception as e:
        raise HTTPException(502, f"The assistant failed: {e}")

    return {
        "answer": result["answer"],
        "sources": sort_cited_first(result["answer"], result["sources"]),
        "tool_calls": result["tool_calls"],
        "filters": filters,
        "mode": request.mode,
    }


def get_source_or_404(file_name):
    if not FILE_NAME_PATTERN.match(file_name):
        raise HTTPException(400, "Invalid file name")
    source = tools.find_cv(file_name)
    if source is None:
        raise HTTPException(404, f"{file_name} is not in the database")
    return source


@app.get("/api/candidates/{file_name}")
def candidate(file_name: str):
    return get_source_or_404(file_name)


@app.get("/api/cvs/{file_name}")
def cv_pdf(file_name: str):
    path = tools.cv_path(get_source_or_404(file_name))
    if not path.exists():
        raise HTTPException(404, "The PDF is not in the data folder")
    return FileResponse(path, media_type="application/pdf")


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
