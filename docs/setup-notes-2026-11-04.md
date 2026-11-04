# Setup notes — 2026-11-04

First machine check of the full stack on Yassine's laptop.

## What we verified

| Check | Result |
|-------|--------|
| GitHub remote | `https://github.com/Nemri-Yassine/cv-screening-project` is up to date |
| Python packages (fastapi, langgraph, mcp) | Installed |
| Docker CLI | Installed (Docker Desktop 29.x) |
| Docker daemon | **Not running** — `docker compose up` fails with `dockerDesktopLinuxEngine` pipe missing |
| `.env` | **Missing** — only `.env.example` is in the repo |
| `data/` with CV PDFs | **Missing** — nothing to ingest yet |
| Frontend `node_modules` | Present from earlier `npm install` |

## Blockers before a real end-to-end demo

1. Start **Docker Desktop** and wait until it is fully up, then `docker compose up -d`.
2. Copy `.env.example` → `.env` and set `GROQ_API_KEY`.
3. Download the Kaggle resume dataset and put the category folders under `data/`.
4. Run `python scripts/check_setup.py` until everything is `OK`.
5. Then: `python ingestion.py` → API → frontend.

## Helper added

`scripts/check_setup.py` prints a checklist so we do not rediscover these gaps every time.
