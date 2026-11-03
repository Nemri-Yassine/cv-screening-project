# CV Screening Assistant

A recruiter asks questions in natural language ("find me IT profiles with Python and 3+ years of experience")
and the assistant searches a database of CVs (PDF) to answer, citing the CVs it used.

**Authors:** [Yassine Nemri](https://github.com/Nemri-Yassine) · Ihab Lamouchi

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the working agreement (daily commits, one change per commit).

## What the project covers

| Requirement | Where |
|---|---|
| RAG + metadata | `ingestion.py` extracts metadata from each CV with the LLM (`metadata_extractor.py`) and stores it in Qdrant; `chat.py` filters on category / years of experience |
| Citations | answers cite CVs as `[10554236.pdf]`; the API returns the list of sources and the web app opens the original PDF |
| LangChain / LangGraph | `chat.py` : RAG graph (extract filters -> retrieve -> grade -> retry without category -> generate); `agent.py` : tool calling agent graph |
| Tool calling / MCP | `tools.py` : 4 tools (search, read CV, compare, list categories), used by the agent and exposed over MCP by `mcp_server.py` |
| Benchmarking | `eval_retrieval.py` (Precision@k, MRR, basic vs advanced RAG) and `eval_generation.py` (LLM as a judge : faithfulness, relevance) |
| Web interface | `api.py` (FastAPI) + `frontend/` (React) |
| SLM fine-tuning (bonus) | `finetune_slm.ipynb` fine-tunes Qwen2.5-0.5B with LoRA to classify CVs, `compare_slm_vs_llm.py` compares it with the Groq LLM |

## Architecture

```
            React (frontend/)  ── /api ──>  FastAPI (api.py)
                                               │
                         ┌─────────────────────┴─────────────────────┐
                 mode "rag"                                    mode "agent"
           chat.py (LangGraph RAG)                   agent.py (LangGraph + tool calling)
                         │                                           │
                         │                          tools.py  <── mcp_server.py (MCP clients)
                         └──────────────> Qdrant (CV profiles + metadata) <──┘
                                               ▲
                     ingestion.py + metadata_extractor.py (Groq LLM) <── data/*.pdf
```

- **RAG pipeline** (`chat.py`) : fixed steps, one retrieval, no memory. Good baseline, used by the evaluations.
- **Agent** (`agent.py`) : the LLM chooses the tools, can chain them (search then read a CV then compare) and keeps the conversation history.

### Tools

| Tool | What it does |
|---|---|
| `search_candidates(query, category, min_years, k)` | semantic search with metadata filters |
| `get_candidate_details(file_name)` | metadata + text of the PDF, for detailed questions |
| `compare_candidates(file_names, required_skills)` | side by side comparison, ranked by matched skills then experience |
| `list_categories()` | number of CVs per category |

## Setup

### 1. Vector DB

1- Open docker (docker desktop for windows)
2- Launch the docker compose using
```bash
docker compose up -d
```
3- Check the Qdrant UI on : localhost:6333/dashboard

### 2. Data

4- Download the dataset at : https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset

5- Create a folder named data : cv-screening-project/data
6- Copy the category folders (ACCOUNTANT, HR, INFORMATION-TECHNOLOGY ...) from `data/data/` of the download inside it.
You should have : data/ACCOUNTANT/10554236.pdf, data/HR/...

7- Copy .env.example to .env and put your Groq API key

### 3. Python

```bash
pip install -r requirements.txt
```

## Running the project

8 - `python metadata_extractor.py` : test the extraction on one CV
9 - `python ingestion.py` : extract the metadata of the CVs and store them in Qdrant (MAX_PER_CATEGORY CVs per category)
10 - `python chat.py` (RAG pipeline) or `python agent.py` (tool calling agent) : ask questions in the terminal, /bye to quit
11 - `python eval_retrieval.py` then `python eval_generation.py`

### Web app

```bash
# terminal 1 : backend on http://localhost:8000 (docs on /docs)
uvicorn api:app --reload --port 8000

# terminal 2 : frontend on http://localhost:5173
cd frontend
npm install
npm run dev
```

For the demo you can also build the frontend once (`npm run build` in `frontend/`) and only run uvicorn :
the app is then served on http://localhost:8000.

API endpoints :

| Method | Route | |
|---|---|---|
| GET | `/api/health` | Qdrant status and number of CVs |
| GET | `/api/categories` | CVs per category |
| POST | `/api/chat` | `{question, mode: "agent" \| "rag", history}` -> `{answer, sources, tool_calls, filters}` |
| GET | `/api/candidates/{file_name}` | metadata of one CV |
| GET | `/api/cvs/{file_name}` | original PDF |

### MCP server

`mcp_server.py` exposes the same tools to any MCP client (stdio). Example for Cursor (`.cursor/mcp.json`) or Claude Desktop :

```json
{
  "mcpServers": {
    "cv-screening": {
      "command": "python",
      "args": ["C:/path/to/cv-screening-project/mcp_server.py"]
    }
  }
}
```

Qdrant must be running. You can also inspect it with `npx @modelcontextprotocol/inspector python mcp_server.py`.

### Tests

```bash
python -m pytest tests -q
```

They use an in-memory Qdrant and a scripted LLM, so no Docker nor Groq key is needed.

## Fine-tuning the SLM

12 - `python build_dataset.py` : creates train.csv and test.csv from the PDFs
13 - Open `finetune_slm.ipynb` on Google Colab (Runtime -> T4 GPU), upload train.csv and test.csv, run all the cells
14 - Unzip the downloaded `slm-cv-classifier.zip` in this folder
15 - `python compare_slm_vs_llm.py`
