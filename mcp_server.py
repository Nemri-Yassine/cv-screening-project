"""
MCP server : exposes the CV database tools to any MCP client (Claude Desktop, Cursor, ...).

Run : python mcp_server.py   (stdio transport, the client starts the process itself)
Qdrant must be running and the CVs ingested.
"""

from mcp.server.mcpserver import MCPServer

import tools

mcp = MCPServer(
    "cv-screening",
    instructions="Search and compare candidates in a database of CVs. Cite candidates with their file name.",
)


@mcp.tool()
def search_candidates(query: str, category: str = "", min_years: int = 0, k: int = 5) -> list[dict]:
    """Search the CV database for candidates matching a job / skills description.

    category is one of the database categories (see list_categories) or "" for all of them.
    """
    return tools.search(query, category, min_years, k)


@mcp.tool()
def get_candidate_details(file_name: str) -> dict:
    """Metadata and text of one CV, e.g. file_name="10554236.pdf"."""
    source = tools.find_cv(file_name)
    if source is None:
        return {"error": f"No CV named {file_name} in the database."}
    return {**source, "cv_text": tools.cv_text(source)}


@mcp.tool()
def compare_candidates(file_names: list[str], required_skills: list[str] | None = None) -> list[dict]:
    """Compare several candidates side by side and rank them by the required skills they have."""
    return tools.compare(file_names, required_skills)


@mcp.tool()
def list_categories() -> dict[str, int]:
    """Job categories of the database with the number of CVs in each one."""
    return tools.category_counts()


if __name__ == "__main__":
    mcp.run()
