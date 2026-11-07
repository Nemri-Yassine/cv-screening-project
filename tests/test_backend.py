"""
Backend tests without Docker nor Groq : an in-memory Qdrant with 3 fake CVs and a scripted LLM.

Run : python -m pytest tests -q
"""

import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("GROQ_API_KEY", "fake-key-for-tests")
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

memory_client = QdrantClient(location=":memory:")
memory_client.create_collection("cvs", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
QdrantVectorStore.from_existing_collection = staticmethod(
    lambda embedding, url, collection_name, **kwargs: QdrantVectorStore(
        client=memory_client, collection_name=collection_name, embedding=embedding
    )
)

import chat  # noqa: E402  (must be imported after the Qdrant patch)

FAKE_CVS = [
    ("111.pdf", "INFORMATION-TECHNOLOGY", "Python Developer", 5, ["Python", "Django", "SQL"]),
    ("222.pdf", "INFORMATION-TECHNOLOGY", "System Administrator", 2, ["Linux", "Networking"]),
    ("333.pdf", "ACCOUNTANT", "Staff Accountant", 7, ["QuickBooks", "Tax returns"]),
]
chat.vector_store.add_documents([
    Document(
        page_content=f"{title}. Skills: {', '.join(skills)}",
        metadata={"file_name": file_name, "category": category, "job_title": title, "years_experience": years,
                  "education_level": "Bachelor", "skills": skills, "summary": f"A {title}"},
    )
    for file_name, category, title, years, skills in FAKE_CVS
])

import agent  # noqa: E402
import api  # noqa: E402
import mcp_server  # noqa: E402
import tools  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class ScriptedLLM:
    """Asks for one search, then answers with a citation."""

    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return AIMessage("", tool_calls=[{
                "name": "search_candidates", "id": "call_1",
                "args": {"query": "python developer", "category": "INFORMATION-TECHNOLOGY", "min_years": 3},
            }])
        assert messages[-1].type == "tool"
        return AIMessage("The best match is [111.pdf].")


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setattr(agent, "llm_with_tools", ScriptedLLM())
    return TestClient(api.app)


def test_search_uses_filters():
    results = tools.search("python developer", category="information-technology", min_years=3)
    assert [source["file_name"] for source in results] == ["111.pdf"]
    assert "_id" not in results[0] and results[0]["profile"]


def test_find_cv():
    assert tools.find_cv("333.pdf")["job_title"] == "Staff Accountant"
    assert tools.find_cv("missing.pdf") is None


def test_compare_ranks_by_required_skills():
    rows = tools.compare(["222.pdf", "111.pdf", "missing.pdf"], ["python", "sql"])
    assert rows[0]["file_name"] == "111.pdf" and rows[0]["skill_score"] == "2/2"
    assert any(row.get("error") == "not found" for row in rows)


def test_category_counts():
    counts = tools.category_counts()
    assert counts["INFORMATION-TECHNOLOGY"] == 2 and counts["ACCOUNTANT"] == 1


def test_agent_chat_returns_tool_calls_and_citations(http):
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    response = http.post("/api/chat", json={"question": "python devs with 3+ years", "mode": "agent", "history": history})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The best match is [111.pdf]."
    assert body["tool_calls"][0]["name"] == "search_candidates"
    assert body["sources"][0]["file_name"] == "111.pdf" and body["sources"][0]["cited"]


def test_api_validation(http):
    assert http.get("/api/health").json() == {"status": "ok", "cv_count": 3}
    assert http.get("/api/candidates/111.pdf").status_code == 200
    assert http.get("/api/candidates/missing.pdf").status_code == 404
    assert http.get("/api/candidates/..%2Fsecret.pdf").status_code in (400, 404)
    assert http.get("/api/cvs/111.pdf").status_code == 404  # no PDF on disk in the tests
    assert http.post("/api/chat", json={"question": ""}).status_code == 422


def test_sources_follow_citation_order_in_the_answer():
    from api import sort_cited_first

    sources = [
        {"file_name": "b.pdf", "job_title": "B"},
        {"file_name": "a.pdf", "job_title": "A"},
        {"file_name": "c.pdf", "job_title": "C"},
    ]
    ordered = sort_cited_first("Best are [a.pdf] then [b.pdf].", sources)
    assert [s["file_name"] for s in ordered] == ["a.pdf", "b.pdf", "c.pdf"]
    assert ordered[0]["citation_index"] == 1 and ordered[0]["cited"]
    assert ordered[2]["citation_index"] is None and not ordered[2]["cited"]


def test_mcp_server_exposes_the_tools():
    async def check():
        listed = await mcp_server.mcp.list_tools()
        assert {tool.name for tool in listed} == {
            "search_candidates", "get_candidate_details", "compare_candidates", "list_categories"
        }
        result = await mcp_server.mcp.call_tool("compare_candidates", {"file_names": ["111.pdf"], "required_skills": ["Django"]})
        assert "111.pdf" in str(result)

    asyncio.run(check())
