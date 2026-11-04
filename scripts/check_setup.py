"""
Quick check before the first end-to-end run.

Run : python scripts/check_setup.py
Exit code 0 = ready to ingest / start the API. Non-zero = something is missing.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ok = True


def check(label: str, passed: bool, hint: str = "") -> None:
    global ok
    mark = "OK" if passed else "MISSING"
    print(f"[{mark}] {label}")
    if not passed:
        ok = False
        if hint:
            print(f"       -> {hint}")


def main() -> int:
    print(f"Project root: {ROOT}\n")

    check(
        ".env with GROQ_API_KEY",
        (ROOT / ".env").exists() and "GROQ_API_KEY=" in (ROOT / ".env").read_text(encoding="utf-8", errors="ignore"),
        "Copy .env.example to .env and put your Groq API key",
    )

    data = ROOT / "data"
    pdfs = list(data.glob("*/*.pdf")) if data.is_dir() else []
    check(
        f"CV dataset in data/ ({len(pdfs)} PDFs found)",
        len(pdfs) > 0,
        "Download the Kaggle resume dataset and copy the category folders into data/",
    )

    docker = shutil.which("docker")
    check("docker CLI installed", docker is not None, "Install Docker Desktop")

    qdrant_up = False
    if docker:
        try:
            import urllib.request

            with urllib.request.urlopen("http://localhost:6333/readyz", timeout=2) as response:
                qdrant_up = response.status == 200
        except Exception:
            qdrant_up = False
    check(
        "Qdrant reachable on localhost:6333",
        qdrant_up,
        "Start Docker Desktop, then: docker compose up -d",
    )

    try:
        import fastapi  # noqa: F401
        import langgraph  # noqa: F401
        import mcp  # noqa: F401

        py_ok = True
    except ImportError:
        py_ok = False
    check("Python packages (fastapi, langgraph, mcp)", py_ok, "pip install -r requirements.txt")

    frontend = ROOT / "frontend" / "node_modules"
    check(
        "Frontend dependencies (frontend/node_modules)",
        frontend.is_dir(),
        "cd frontend && npm install",
    )

    print()
    if ok:
        print("Setup looks good. Next:")
        print("  python ingestion.py")
        print("  uvicorn api:app --reload --port 8000")
        print("  cd frontend && npm run dev")
        return 0

    print("Fix the MISSING items above, then run this script again.")
    return 1


if __name__ == "__main__":
    # load_dotenv is optional here; we only check the file exists
    os.chdir(ROOT)
    sys.exit(main())
