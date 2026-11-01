"""
Tools of the CV database.

The plain functions (search, find_cv, ...) are used by the API and by the MCP server (mcp_server.py),
the @tool versions at the bottom are given to the LangGraph agent (agent.py).
"""

import json
from pathlib import Path

from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
from qdrant_client.models import Filter, FieldCondition, MatchValue

from chat import vector_store, build_filter, doc_to_source, SearchFilters, CATEGORIES, COLLECTION_NAME

DATA_PATH = Path(__file__).parent / "data"
MAX_RESULTS = 10
MAX_CV_CHARS = 4000

client = vector_store.client


def _file_filter(file_name):
    return Filter(must=[FieldCondition(key="metadata.file_name", match=MatchValue(value=file_name))])


def search(query, category="", min_years=0, k=5):
    """Semantic search on the CV profiles, with optional category / experience filters."""
    filters = SearchFilters(search_query=query, category=category.upper(), min_years=min_years)
    documents = vector_store.similarity_search(query, k=min(k, MAX_RESULTS), filter=build_filter(filters))
    return [doc_to_source(doc) for doc in documents]


def find_cv(file_name):
    """Metadata of one CV, or None if the file name is not in the database."""
    points, _ = client.scroll(collection_name=COLLECTION_NAME, scroll_filter=_file_filter(file_name), limit=1)
    if not points:
        return None
    return {**points[0].payload["metadata"], "profile": points[0].payload["page_content"]}


def cv_path(source):
    return DATA_PATH / source["category"] / source["file_name"]


def cv_text(source, max_chars=MAX_CV_CHARS):
    """Raw text of the PDF, '' if the file is not on disk."""
    path = cv_path(source)
    if not path.exists():
        return ""
    pages = PyPDFLoader(str(path)).load()
    return "\n".join(page.page_content for page in pages)[:max_chars]


def category_counts():
    """Number of CVs stored in Qdrant for each category."""
    counts = {}
    for category in CATEGORIES:
        category_filter = Filter(must=[FieldCondition(key="metadata.category", match=MatchValue(value=category))])
        counts[category] = client.count(COLLECTION_NAME, count_filter=category_filter, exact=True).count
    return counts


def _skill_matches(required, skills):
    required, skills = required.lower(), [skill.lower() for skill in skills]
    return any(required in skill or skill in required for skill in skills)


def compare(file_names, required_skills=None):
    """Side by side comparison of CVs, with the required skills each candidate has or misses."""
    required_skills = required_skills or []
    rows = []
    for file_name in file_names:
        source = find_cv(file_name)
        if source is None:
            rows.append({"file_name": file_name, "error": "not found"})
            continue
        matched = [skill for skill in required_skills if _skill_matches(skill, source["skills"])]
        rows.append({
            **source,
            "matched_skills": matched,
            "missing_skills": [skill for skill in required_skills if skill not in matched],
            "skill_score": f"{len(matched)}/{len(required_skills)}" if required_skills else None,
        })
    # best candidates first : most matched skills, then most experience
    return sorted(rows, key=lambda row: (len(row.get("matched_skills", [])), row.get("years_experience", 0)), reverse=True)


# LangChain tools : the content goes to the LLM, the artifact (list of sources) is kept for the citations

@tool(response_format="content_and_artifact")
def search_candidates(query: str, category: str = "", min_years: int = 0, k: int = 5):
    """Search the CV database for candidates matching a job / skills description.

    Args:
        query: short description of the profile, e.g. "python developer with django experience"
        category: one of the database categories (e.g. INFORMATION-TECHNOLOGY), or "" for all categories
        min_years: minimum years of experience, 0 for no minimum
        k: number of candidates to return (max 10)
    """
    sources = search(query, category, min_years, k)
    if not sources:
        return "No candidate found, try a broader query or remove the filters.", []
    return json.dumps(sources, ensure_ascii=False), sources


@tool(response_format="content_and_artifact")
def get_candidate_details(file_name: str):
    """Read the full CV of one candidate (metadata + text of the PDF).
    Use it to answer detailed questions about a candidate (a tool, a degree, a company, ...).

    Args:
        file_name: the CV file name, e.g. "10554236.pdf"
    """
    source = find_cv(file_name)
    if source is None:
        return f"No CV named {file_name} in the database.", []
    details = {**source, "cv_text": cv_text(source)}
    return json.dumps(details, ensure_ascii=False), [source]


@tool(response_format="content_and_artifact")
def compare_candidates(file_names: list[str], required_skills: list[str] | None = None):
    """Compare several candidates side by side and rank them by the required skills they have.

    Args:
        file_names: CV file names to compare, e.g. ["10554236.pdf", "12345678.pdf"]
        required_skills: skills the recruiter needs, e.g. ["Python", "SQL"]
    """
    rows = compare(file_names, required_skills)
    return json.dumps(rows, ensure_ascii=False), [row for row in rows if "error" not in row]


@tool
def list_categories() -> str:
    """List the job categories of the database with the number of CVs in each one."""
    return json.dumps(category_counts())


TOOLS = [search_candidates, get_candidate_details, compare_candidates, list_categories]
