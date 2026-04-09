# Building Code Web Project

A pipeline that extracts, structures, and serves **building code PDFs** as a fully navigable, searchable, and cross-referenced web application. Feed it any structured building code PDF and get an interactive browser with resolved clause references, inline equations, tables, and appendix note links.

---

## Overview

Building codes are dense, hierarchically structured documents filled with numbered clauses, cross-references, equations, and tables. This project automates their digitisation into a structured JSON data model and serves them through a Streamlit web viewer backed by a FastAPI REST API.

```
PDF  →  Datalab Marker API  →  Structure Parser  →  Reference Linker  →  JSON
                                                                           ↓
                                                          FastAPI (port 8000)
                                                                           ↓
                                                        Streamlit Viewer (port 8501)
```

---

## Features

- **PDF extraction** via [Datalab Marker API](https://www.datalab.to) with local result caching
- **Hierarchical parsing** — Division → Part → Section → Subsection → Clause → Sub-clause → Table / Figure / Equation
- **Notes section extraction** — "Notes to Part N" segments parsed into dedicated `SEC-NOTES-*` sections inside each Part, holding `CL-NOTE-*` note clauses at the same level as regular code sections
- **Cross-reference resolution** — `Sentence 4.1.6.5.(1)`, `Table 4.1.3.2.-A`, `Figure 4.1.6.5.-A` resolved to clickable links (84.7% resolution rate)
- **Appendix note resolution** — `(See Note A-4.1.6.16.(6).)` resolved to `CL-NOTE-*` clause IDs and rendered as navigable buttons (99.8% resolution rate)
- **Inline KaTeX math** — equations rendered in-browser
- **Multi-row table headers** — colspan / rowspan parsed correctly; cross-page table fragments merged
- **Full-text search** across all clause titles and content
- **REST API** — headless programmatic access to the structured document
- **Optional AI enhancement** — Claude adds semantic column labels to tables

---

## Tech Stack

| Layer | Technology |
|---|---|
| PDF Extraction | [Datalab Marker API](https://www.datalab.to) |
| AI Enhancement | Anthropic Claude (`claude-sonnet-4-20250514`) |
| Backend API | FastAPI + Uvicorn (port 8000) |
| Viewer | Streamlit (port 8501) |
| Storage | JSON files + JPEG figures |
| Runtime | Python 3.10+ |

---

## Project Structure

```
buildingCodeWebProject/
├── main.py                        # Pipeline entry point
├── viewer_streamlit.py            # Streamlit document viewer
├── requirements.txt
├── .env                           # API keys (not committed)
│
├── ingestion/
│   └── datalab_client.py          # PDF → Datalab API → cached raw JSON
│
├── parser/
│   ├── structure_parser.py        # Datalab JSON → Document tree
│   ├── reference_linker.py        # Resolve cross-references & appendix notes
│   └── ai_enhancer.py             # Optional Claude table enhancement
│
├── storage/
│   ├── document_store.py          # save / load / search index helpers
│   ├── raw_{pdf_stem}.json        # Cached raw Datalab extraction
│   ├── figures/                   # Extracted images (JPEG, hash-named)
│   └── output/
│       ├── structured_document.json   # Final processed output
│       └── flagged_issues.json        # QA flags from viewer
│
└── api/
    └── main.py                    # FastAPI REST API
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- A [Datalab API key](https://www.datalab.to/app/keys)
- An [Anthropic API key](https://console.anthropic.com/api-keys) *(optional — only needed for the `--ai` flag)*

### 2. Clone and install

```bash
git clone <repo-url>
cd buildingCodeWebProject

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API keys

Create a `.env` file in the project root:

```env
DATALAB_API_KEY=your_datalab_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 4. Process a PDF

```bash
python main.py path/to/building_code.pdf
```

Output: `storage/output/structured_document.json`

### 5. Launch the viewer

```bash
streamlit run viewer_streamlit.py
```

Open **http://localhost:8501**

### 6. (Optional) Start the REST API

```bash
uvicorn api.main:app --reload --port 8000
```

Interactive docs at **http://localhost:8000/docs**

---

## Pipeline Flags

```bash
# Standard run — uses cached Datalab result if available
python main.py building_code.pdf

# Force re-extraction (re-calls Datalab API, useful after PDF changes)
python main.py building_code.pdf --force-extract

# Enable Claude AI table column labelling
python main.py building_code.pdf --ai
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/document` | Full document tree |
| GET | `/document/summary` | Lightweight navigation tree (no clause body) |
| GET | `/section/{section_id}` | Single section with all its clauses |
| GET | `/clause/{clause_id}` | Single clause with breadcrumb context |
| GET | `/search?q=term` | Full-text search across all content (capped at 50) |
| GET | `/references/{node_id}` | Reverse lookup: which clauses reference this node |

---

## Streamlit Viewer

The viewer (`viewer_streamlit.py`) is a single-page **Extraction Statistics** dashboard:

| Section | Description |
|---|---|
| Top-level counts | Pages, Parts, Sections, Clauses, Equations, Figures, Tables |
| Reference Resolution | Found / Resolved / Rate for cross-references and appendix note refs |
| Per-Part Breakdown | Sections, Clauses, Equations, Figures, Tables per Part |
| Downloads | `structured_document.json` and raw Datalab JSON download buttons |

---

## Supported Document Types

The parser targets structured legislative/regulatory documents with:

- Numbered hierarchical clauses (`4.1.6.5.(1)`)
- Internal cross-references (`Sentence X`, `Article X`, `Table X`, `Figure X`)
- Multi-level HTML tables with colspan/rowspan headers
- Inline and display LaTeX equations
- Appendix notes (`See Note A-4.1.6.16.(6).`)
- "Notes to Part N" segments (extracted into dedicated section-level notes blocks)

The **full British Columbia Building Code 2024 (BCBC 2024, 1906 pages, Divisions A/B/C)** is the primary development and validation document.

---

## Key Notes

- The Datalab response is cached on first run — subsequent runs cost nothing.
- The system processes **one document at a time**. Running on a new PDF overwrites `structured_document.json`.
- The Streamlit viewer reads the JSON directly — no API server is required to run it.
- The FastAPI server is optional and provided for programmatic / headless access.

---

## Documentation

For full technical documentation including data model, parser internals, and configuration details see **[GUIDE.md](GUIDE.md)**.

For developer/AI-assistant context see **[CLAUDE.md](CLAUDE.md)**.
