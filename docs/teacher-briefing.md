# Teacher briefing — CV Screening Assistant

**Repo:** https://github.com/Nemri-Yassine/cv-screening-project  
**Team:** Yassine Nemri · Ihab Lamouchi  
**One sentence:** A recruiter asks in natural language; we search a PDF CV database with RAG + LangGraph, cite the CVs, and show answers in a React app (plus tool calling / MCP).

Use this page to talk. Open the files in Cursor when the teacher asks “where is the code?”.

---

## Big picture (draw this on the board)

```mermaid
flowchart LR
  PDF[PDF CVs] --> META[LLM extracts metadata]
  META --> Q[(Qdrant)]
  Q --> RAG[LangGraph RAG]
  Q --> TOOLS[Tools + Agent]
  TOOLS --> MCP[MCP server]
  RAG --> API[FastAPI]
  TOOLS --> API
  API --> UI[React web UI]
```

**Teacher mapping (mandatory features):**

| They ask for | We say | File |
|---|---|---|
| RAG + metadata + citations | Yes | `ingestion.py`, `metadata_extractor.py`, `chat.py` |
| LangChain / LangGraph | Yes | `chat.py`, `agent.py` |
| Tool calling / MCP | Yes | `tools.py`, `agent.py`, `mcp_server.py` |
| Benchmarking | Yes | `eval_retrieval.py`, `eval_generation.py` |
| Web interface | Yes | `api.py` + `frontend/` |
| Fine-tuning (optional) | Bonus done | `finetune_slm.ipynb` |

---

## Week 1 = the foundation (explain THIS first)

Week 1 is **not** the fancy agent yet. It is: **ingest CVs → store in Qdrant → ask questions with a fixed RAG graph**.

```mermaid
flowchart TD
  A[PDF in data/CATEGORY/] --> B[ingestion.py loads text]
  B --> C[metadata_extractor.py calls LLM]
  C --> D[job title, years, skills, summary...]
  D --> E[Embed short profile MiniLM]
  E --> F[(Qdrant collection cvs)]

  G[Recruiter question] --> H[chat.py LangGraph]
  H --> I[1 extract filters LLM]
  I --> J[2 retrieve from Qdrant]
  J --> K{3 good candidates?}
  K -->|no| L[drop category filter, retry]
  L --> J
  K -->|yes| M[4 generate answer + citations]
```

### Script you can say out loud

1. **Ingestion:** each CV PDF is read; an LLM extracts structured metadata (title, years, skills…).
2. We do **not** embed the whole messy PDF. We embed a short profile string (title + summary + skills) → better search.
3. Everything goes into **Qdrant** with metadata filters (category, years).
4. At question time, **LangGraph** runs fixed steps: extract filters → search → grade → maybe retry without category → answer with `[filename.pdf]` citations.

### Where the LLM is called (Week 1)

| Step | What the LLM does | File | Lines |
|---|---|---|---|
| Create Groq client | model `openai/gpt-oss-120b` | `metadata_extractor.py` | 19–23 |
| Extract CV fields | structured output `CVMetadata` | `metadata_extractor.py` | 36–41 |
| Call extraction from ingest | `extract_metadata(text)` | `ingestion.py` | 69 |
| Create Groq client (chat) | model `openai/gpt-oss-20b` | `chat.py` | 50–53 |
| Extract search filters | `filter_chain.invoke(...)` | `chat.py` | 96, 147 |
| Grade retrieved CVs | `grade_chain.invoke(...)` | `chat.py` | 97, 182–186 |
| Write the final answer | `answer_chain.invoke(...)` | `chat.py` | 98, 168–173 |
| Vector search (no LLM) | `similarity_search` | `chat.py` | 152–157 |
| Graph wiring | `StateGraph` nodes/edges | `chat.py` | 191–204 |

**Tip:** open `chat.py` around line 191 — the graph is the whole Week‑1 story in one place.

### Metadata fields (say this if asked “what metadata?”)

From `metadata_extractor.py` (`CVMetadata`): `job_title`, `years_experience`, `education_level`, `skills`, `summary`  
Plus folder name = `category`, and `file_name` for citations.  
`years_experience` is a **float** (example: 4.5). Groq rejects the structured answer when the field is an `int`.

---

## After Week 1 (short — only if they ask)

```mermaid
flowchart LR
  W1[Week 1 RAG graph] --> W2[Tools + Agent]
  W2 --> W3[MCP]
  W3 --> W4[React + API]
  W4 --> W5[Evals + SLM bonus]
```

| Layer | One line | Open this |
|---|---|---|
| Tools | search / read CV / compare / list categories | `tools.py` (~92–138 `@tool`) |
| Agent | LLM chooses tools (`bind_tools`) | `agent.py` 39–48, 52–60 |
| MCP | same tools for Claude/Cursor | `mcp_server.py` |
| API | `/api/chat` agent or rag mode | `api.py` 66–87 |
| UI | chat + sources + PDF panel | `frontend/src/App.tsx` |
| Retrieval eval | Precision@k, MRR | `eval_retrieval.py` |
| Generation eval | LLM-as-judge | `eval_generation.py` |
| SLM bonus | LoRA on Qwen 0.5B | `finetune_slm.ipynb` |

### Agent LLM call (if they ask tool calling)

- Create LLM: `agent.py` **39–43**
- Bind tools: `agent.py` **44**
- Call LLM: `agent.py` **48** (`llm_with_tools.invoke`)
- Loop tools ↔ agent: `agent.py` **52–60**

---

## Same shape as the course repo

Reference: [Nadjib23/AI-Engineering-Course](https://github.com/Nadjib23/AI-Engineering-Course), especially `labs/99-exercices/invoices_extractor/` and `labs/04-rag/`.

| His file | Our file | Same idea |
|---|---|---|
| `src/metadata_extractor.py` | `metadata_extractor.py` | Pydantic model, Groq, `prompt \| llm.with_structured_output(...)` |
| `src/ingesting.py` | `ingestion.py` | PyPDFLoader, MiniLM, Qdrant on `localhost:6333`, skip files already stored, metadata on the point |
| `src/chat.py` | `chat.py` | Same prompt style, same collection connect, metadata `Filter` / `FieldCondition` |
| `08` / `09` tool labs | `tools.py`, `agent.py` | `@tool`, `bind_tools`, tool loop. Ours is a LangGraph `ToolNode` |
| `labs/04-rag/docker-compose.yml` | `docker-compose.yml` | Qdrant in Docker |
| `labs/05-Evaluation` | `eval_retrieval.py`, `eval_generation.py` | Precision@k plus a generation judge |

Two choices that are **not** a copy of the invoice exercise, on purpose:

- He chunks the full PDF and searches **hybrid** (dense MiniLM + BM25). We store **one short profile per CV** and search **dense** only, because MiniLM only reads about 256 tokens and a CV is longer than that.
- He demos with **Streamlit**. The course asked for a web interface, so we use **FastAPI + React**, and the same tools are also on MCP.

---

## Progress status (honest)

| Done in code | Still to finish for the course |
|---|---|
| RAG, metadata, citations | Full run on your PC: Docker/Qdrant + `.env` + `data/` PDFs |
| LangGraph RAG + agent + MCP | Live demo with real Groq answers |
| FastAPI + React UI | Technical report PDF + presentation slides |
| Eval scripts + SLM notebook | Daily commits continuing (see `PHASES.md`) |
| GitHub repo with history | — |

**Current week story for the teacher:**  
“The pipeline follows the course labs: metadata extractor, ingestion into Qdrant, then a LangGraph chat with filters and citations. On 23 Nov we fixed years of experience as a float, because Groq was rejecting 4.5 years. Retrieval stays dense on a short profile; hybrid BM25 is in his invoice lab, not in this project.”

---

## 30-second demo path (when stack is up)

```bash
docker compose up -d
python scripts/check_setup.py
python ingestion.py
uvicorn api:app --reload --port 8000
# other terminal:
cd frontend && npm run dev
```

Ask in the UI: *“Find IT profiles with Python and at least 3 years of experience”*  
→ answer should cite `[something.pdf]` and show source cards.
