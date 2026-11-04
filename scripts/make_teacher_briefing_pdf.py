"""Build docs/teacher-briefing.pdf (short teacher cheat sheet)."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "teacher-briefing.pdf"

NAVY = colors.HexColor("#1c2033")
MUTED = colors.HexColor("#5b6178")
PRIMARY = colors.HexColor("#4f46e5")
SOFT = colors.HexColor("#eef0ff")
LINE = colors.HexColor("#d8dce8")
WHITE = colors.white


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18,
            textColor=NAVY, spaceAfter=4, alignment=TA_CENTER,
        ),
        "sub": ParagraphStyle(
            "sub", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=10, leading=12,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=12,
            textColor=PRIMARY, spaceBefore=12, spaceAfter=6, leading=14,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=10.5,
            textColor=NAVY, spaceBefore=8, spaceAfter=4, leading=13,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            textColor=NAVY, leading=12, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            textColor=NAVY, leading=12,
        ),
        "code": ParagraphStyle(
            "code", parent=base["Code"], fontName="Courier", fontSize=7.5,
            textColor=NAVY, leading=10, backColor=SOFT, leftIndent=4, rightIndent=4,
            spaceBefore=4, spaceAfter=6,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontName="Helvetica", fontSize=8,
            textColor=NAVY, leading=10,
        ),
        "cell_b": ParagraphStyle(
            "cell_b", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8,
            textColor=NAVY, leading=10,
        ),
        "say": ParagraphStyle(
            "say", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=9,
            textColor=NAVY, leading=12, leftIndent=6, rightIndent=6,
            spaceBefore=4, spaceAfter=6, backColor=SOFT, borderPadding=6,
        ),
    }


def table(rows, col_widths):
    header_style = ParagraphStyle(
        "hdr", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, leading=10,
    )
    cell = styles()["cell"]
    data = [[Paragraph(str(c), header_style) for c in rows[0]]]
    data += [[Paragraph(str(c), cell) for c in row] for row in rows[1:]]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SOFT]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build():
    s = styles()
    story = []
    story.append(Paragraph("CV Screening Assistant — Teacher briefing", s["title"]))
    story.append(Paragraph(
        "Yassine Nemri · Ihab Lamouchi<br/>"
        "https://github.com/Nemri-Yassine/cv-screening-project",
        s["sub"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=8))

    story.append(Paragraph(
        "<b>One sentence:</b> A recruiter asks in natural language; we search a PDF CV "
        "database with RAG + LangGraph, cite the CVs, and show answers in a React app "
        "(plus tool calling / MCP).",
        s["body"],
    ))

    story.append(Paragraph("1. Big picture", s["h1"]))
    story.append(Preformatted(
        "  PDF CVs  -->  LLM extracts metadata  -->  Qdrant\n"
        "                                              |\n"
        "                    +-------------------------+-------------------------+\n"
        "                    |                                                   |\n"
        "             LangGraph RAG                                    Tools + Agent --> MCP\n"
        "                    |                                                   |\n"
        "                    +------------------>  FastAPI  <--------------------+\n"
        "                                             |\n"
        "                                          React UI",
        s["code"],
    ))

    story.append(Paragraph("Teacher checklist (mandatory features)", s["h2"]))
    story.append(table([
        ["They ask for", "We say", "Open this file"],
        ["RAG + metadata + citations", "Yes", "ingestion.py, metadata_extractor.py, chat.py"],
        ["LangChain / LangGraph", "Yes", "chat.py, agent.py"],
        ["Tool calling / MCP", "Yes", "tools.py, agent.py, mcp_server.py"],
        ["Benchmarking", "Yes", "eval_retrieval.py, eval_generation.py"],
        ["Web interface", "Yes", "api.py + frontend/"],
        ["Fine-tuning (optional)", "Bonus done", "finetune_slm.ipynb"],
    ], [4.8 * cm, 2.8 * cm, 9.2 * cm]))

    story.append(Paragraph("2. Week 1 — explain THIS first", s["h1"]))
    story.append(Paragraph(
        "Week 1 is the foundation: ingest CVs → store in Qdrant → ask questions with a "
        "<b>fixed RAG LangGraph</b> (not the fancy agent yet).",
        s["body"],
    ))
    story.append(Preformatted(
        "  data/CATEGORY/*.pdf\n"
        "         |\n"
        "         v\n"
        "  ingestion.py  -->  metadata_extractor.py (LLM)  -->  embed short profile  -->  Qdrant\n"
        "\n"
        "  Recruiter question\n"
        "         |\n"
        "         v\n"
        "  chat.py LangGraph:\n"
        "    1 extract filters (LLM) --> 2 retrieve Qdrant --> 3 grade?\n"
        "         |                                         |\n"
        "         |                              no: drop category, retry\n"
        "         |                                         |\n"
        "         +---------------- yes ------------------> 4 generate answer + [file.pdf]",
        s["code"],
    ))

    story.append(Paragraph("Say this out loud", s["h2"]))
    story.append(Paragraph(
        "1) Each CV PDF is read; an LLM extracts structured metadata "
        "(title, years, skills…).<br/>"
        "2) We embed a short profile (not the whole messy PDF) → better search.<br/>"
        "3) Everything goes into Qdrant with filters (category, years).<br/>"
        "4) LangGraph runs: extract filters → search → grade → maybe retry → "
        "answer with [filename.pdf] citations.",
        s["say"],
    ))

    story.append(Paragraph("Where the LLM is called (Week 1)", s["h2"]))
    story.append(table([
        ["Step", "File", "Lines"],
        ["Create Groq client (metadata)", "metadata_extractor.py", "18–22"],
        ["Extract CV fields (structured)", "metadata_extractor.py", "35–40"],
        ["Call extraction during ingest", "ingestion.py", "69"],
        ["Create Groq client (chat)", "chat.py", "50–53"],
        ["Extract search filters", "chat.py", "96, 147"],
        ["Grade retrieved CVs", "chat.py", "97, 182–186"],
        ["Write final answer", "chat.py", "98, 168–173"],
        ["Vector search (no LLM)", "chat.py", "152–157"],
        ["Graph wiring (best to show)", "chat.py", "191–204"],
    ], [6.5 * cm, 5.5 * cm, 4.8 * cm]))
    story.append(Paragraph(
        "<b>Tip:</b> open <b>chat.py</b> around line <b>191</b> — the whole Week‑1 story is there.",
        s["body"],
    ))

    story.append(Paragraph("Metadata fields", s["h2"]))
    story.append(Paragraph(
        "From <b>metadata_extractor.py</b> (<b>CVMetadata</b>): job_title, years_experience, "
        "education_level, skills, summary. Plus folder name = category, and file_name for citations.",
        s["body"],
    ))

    story.append(Paragraph("3. After Week 1 (only if they ask)", s["h1"]))
    story.append(table([
        ["Layer", "One line", "Open this"],
        ["Tools", "search / read CV / compare / list categories", "tools.py (~92–138)"],
        ["Agent", "LLM chooses tools (bind_tools)", "agent.py 39–48, 52–60"],
        ["MCP", "same tools for Claude / Cursor", "mcp_server.py"],
        ["API", "/api/chat agent or rag mode", "api.py 66–87"],
        ["UI", "chat + sources + PDF panel", "frontend/src/App.tsx"],
        ["Retrieval eval", "Precision@k, MRR", "eval_retrieval.py"],
        ["Generation eval", "LLM-as-judge", "eval_generation.py"],
        ["SLM bonus", "LoRA on Qwen 0.5B", "finetune_slm.ipynb"],
    ], [3.2 * cm, 7.2 * cm, 6.4 * cm]))

    story.append(Paragraph("4. Honest progress", s["h1"]))
    story.append(table([
        ["Done in code", "Still to finish"],
        ["RAG, metadata, citations", "Live run: Qdrant + .env + data/ PDFs"],
        ["LangGraph RAG + agent + MCP", "Live demo with real Groq answers"],
        ["FastAPI + React UI", "Technical report PDF + slides"],
        ["Eval scripts + SLM notebook", "Keep daily commits (PHASES.md)"],
        ["GitHub repo with history", "—"],
    ], [8.4 * cm, 8.4 * cm]))

    story.append(Paragraph(
        "<b>Progress line to say:</b> “We built and published the core RAG pipeline "
        "(ingest → Qdrant → LangGraph chat). We added a setup checker after verifying "
        "the machine. Next we test the tool-calling agent with real API calls and polish the UI.”",
        s["say"],
    ))

    story.append(Paragraph("5. Demo commands (when stack is up)", s["h1"]))
    story.append(Preformatted(
        "docker compose up -d\n"
        "python scripts/check_setup.py\n"
        "python ingestion.py\n"
        "uvicorn api:app --reload --port 8000\n"
        "cd frontend && npm run dev\n"
        "\n"
        'Ask: "Find IT profiles with Python and at least 3 years of experience"',
        s["code"],
    ))

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="CV Screening Assistant — Teacher briefing",
        author="Yassine Nemri, Ihab Lamouchi",
    )
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    build()
