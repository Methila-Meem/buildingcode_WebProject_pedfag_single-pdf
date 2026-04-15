# Building Code Web Project — Context for Claude

## Project Purpose
A pipeline that extracts, structures, and serves **building code PDFs** (e.g. BCBC 2024, full 1906-page multi-division document). The pipeline produces a structured JSON document that can be queried via a REST API and inspected via a Streamlit statistics viewer.

---

## Tech Stack
| Layer | Technology |
|---|---|
| PDF Extraction | Datalab Marker API (async job, JSON output) |
| AI Enhancement | Anthropic Claude (`claude-sonnet-4-20250514`) via `anthropic` SDK |
| Backend API | FastAPI + Uvicorn (port 8000) |
| Viewer | Streamlit (`viewer_streamlit.py`) on port 8501 — Extraction Statistics only |
| Storage | JSON files (`storage/output/structured_document.json`) + JPEG figures (`storage/figures/`) |
| Env | Python venv (`.venv`), secrets in `.env` |

**Dependencies** (`requirements.txt`): `requests`, `anthropic`, `pdfplumber`, `pymupdf`, `fastapi`, `uvicorn`, `python-multipart`, `python-dotenv`, `streamlit`, `pandas`

> **Note:** `pdfplumber` and `pymupdf` are listed in `requirements.txt` but are **not imported anywhere** in the current codebase. The pipeline uses the Datalab API for PDF extraction. These are legacy dependencies from an earlier approach and can be removed.

---

## Project File Map
```
buildingCodeWebProject/
├── main.py                                    # CLI pipeline entry point
├── viewer_streamlit.py                        # Streamlit extraction statistics viewer
├── .env                                       # DATALAB_API_KEY, ANTHROPIC_API_KEY
├── requirements.txt
├── bcbc_2024_web_version_revision2.pdf        # Full BCBC 2024 (1906 pages, primary input)
├── bcbc_2024_Part4-509-654.pdf                # Legacy sample (Part 4 only, 146 pages)
│
├── docs/
│   ├── GUIDE.docx
│   └── GUIDE.html
│
├── ingestion/
│   └── datalab_client.py          # Submit PDF → poll Datalab API → cache → return JSON
│
├── parser/
│   ├── structure_parser.py        # Datalab JSON → Document tree (dataclasses)
│   ├── reference_linker.py        # Resolve cross-references + appendix note refs
│   └── ai_enhancer.py             # Claude calls for table labeling, block classification
│
├── storage/
│   ├── document_store.py          # save_document / load_document / build_search_index
│   ├── raw_{pdf_stem}.json        # Cached raw Datalab API response
│   ├── figures/                   # Extracted images saved as JPEG (hash-named)
│   └── output/
│       ├── structured_document.json   # Final processed document
│       └── flagged_issues.json        # QA flags (written by viewer)
│
└── api/
    └── main.py                    # FastAPI app — serves structured document via REST
```

---

## Data Model (Document Hierarchy)

Part-level content uses the full legal hierarchy. Each level is an explicit node — sentences, clauses, and subclauses are **not** flattened into a `content[]` array.

```
Document
  title, source_pdf, total_pages, _stats
  ├── preface   (Preface)
  ├── divisions (Division[])
  │     └── Division  (id: DIV-B)
  │           └── Part  (id: PART-B-4, number: "4", title: "Structural Design")
  │                 └── Section  (id: SEC-4-1, number: "4.1")
  │                       └── Subsection  (id: SUBSEC-4-1-1, number: "4.1.1")
  │                             └── Article  (id: ART-4-1-1-3, number: "4.1.1.3", title: "...")
  │                                   ├── sentences[]
  │                                   │     └── Sentence  (id: SENT-4-1-1-3-1, number: "4.1.1.3.(1)")
  │                                   │           ├── content: str   — intro text before clauses
  │                                   │           ├── clauses[]
  │                                   │           │     └── Clause  (id: CLAUSE-4-1-1-3-1-a)
  │                                   │           │           ├── content: str
  │                                   │           │           └── subclauses[]
  │                                   │           │                 └── Subclause  (id: SUBCLAUSE-...-i)
  │                                   │           │                       └── content: str
  │                                   │           ├── tables[], figures[], equations[], references[]
  │                                   ├── content[]  — ContentItem list (notes/fallback only)
  │                                   ├── tables[], figures[], equations[], references[]
  │                                   └── note_refs[]  (added dynamically by reference_linker.py)
  └── conversion_factors (ConversionFactors)
```

**Notes sections** (Notes to Part N) use `Article` nodes with `content[]` (no sentence structure).
**Appendix sections** use the same Article/Sentence/Clause/Subclause hierarchy as Parts.

**`_stats` on Document (added by `reference_linker.py`):**
```python
{
    "total_references": 2945,
    "resolved_references": 2867,
    "resolution_rate_pct": 97.4,
    "total_note_refs": 922,
    "resolved_note_refs": 920,
    "note_resolution_rate_pct": 99.8,
}
```
Unresolved references (~2.6%) are expected — they point to other PDFs in the BCBC series (external volumes). Unresolved note refs (0.2%) are genuine external appendix notes not in this PDF.

---

## Pipeline Steps (`main.py run_pipeline`)
1. **Ingest** — `ingestion/datalab_client.extract_pdf(pdf_path, force_extract)` → submits PDF, polls until done, saves `storage/raw_{pdf_stem}.json` (cached; skipped on re-runs unless `--force-extract`)
2. **Parse** — `parser/structure_parser.parse_datalab_output(result, source_pdf, figures_dir)` → builds Document tree; extracts images to `storage/figures/`
3. **Link** — `parser/reference_linker.link_references(doc)` → regex-scans clause content, resolves cross-references and `See Note A-...` refs, writes `_stats`
4. **Enhance** *(optional, `--ai` flag)* — `parser/ai_enhancer.enhance_document(doc)` → Claude labels table columns semantically, storing `column_semantics[]` on each table
5. **Save** — `storage/document_store.save_document(doc)` → writes `structured_document.json`

---

## Datalab Client (`ingestion/datalab_client.py`)

**API parameters sent:**
```python
{ "output_format": "json", "use_llm": "true", "extract_images": "false" }
```
- Endpoint: `https://www.datalab.to/api/v1/marker`
- Poll interval: 5 s, max wait: 300 s, submit timeout: 60 s
- Cache path: `storage/raw_{pdf_stem}.json` — skip with `--force-extract`
- Raises `EnvironmentError` if `DATALAB_API_KEY` missing or placeholder
- Raises `TimeoutError` if polling exceeds max_wait

---

## Structure Parser (`parser/structure_parser.py`)

### Key HTML Processing Functions

| Function | Purpose |
|---|---|
| `inline_math_to_markdown(html)` | Converts `<math>` tags to `$...$` inline notation; strips remaining HTML → single markdown string |
| `extract_math(html)` | Returns **list** of LaTeX strings (one per `<math>` tag) — each becomes a separate Equation ContentItem |
| `listgroup_to_lines(html)` | Preserves `<math>` as `$...$`, strips other HTML, inserts newlines before `<li>` opening tags and after `</li>` closing tags so nested list items always start on their own line |
| `parse_table_html(html)` | Parses HTML tables with multi-row `<thead>` colspan/rowspan, `<tbody>` rowspan carry, bbox-based empty-cell carry, final-row sub-label skip, and spanning-rows last-row exception |
| `strip_html(html)` | Removes tags, decodes entities, normalizes whitespace |
| `_strip_html_keep_text(html)` | Strips all HTML **except** `<math>` markers; used when splitting inline-math blocks |
| `split_inline_math(html)` | Legacy compatibility shim — calls `inline_math_to_markdown()` and returns `[{type:"text", value:...}]` |
| `extract_alt_text(html)` | Extracts the `alt` attribute from an `<img>` tag; falls back to `strip_html()` |
| `parse_heading(html)` | Extracts `(level: int, plain_text: str)` from `<h1>–<h6>` tags; **returns level=0 for untagged SectionHeader blocks** |
| `save_image(image_key, b64, figures_dir)` | Decodes base64, saves as JPEG to `storage/figures/{image_key}` |

### `StructureParser` Class

**Attributes:**
- `source_pdf`, `figures_dir` — set in `__init__`
- `_auto_clause_counter`, `_table_counter`, `_equation_counter`, `_figure_counter` — global counters
- `_images_dict` — populated from `datalab_result["images"]` before flattening
- `_page_objects` — raw page list from Datalab JSON; used by `_resolve_hier_target()` to look up block content by `/page/{idx}/{type}/{child}` path
- `_clause_index` — `{clause_id → Clause}` dict; populated by `_make_clause()`; used by `_resolve_hier_target()` for fast lookup
- `_subsec_index` — `{subsec_id → Subsection}` dict; populated by `_make_subsection()`
- `_section_index` — `{sec_id → Section}` dict; populated by `_make_section()`
- `_notes_section_index` — `{"SEC-NOTES-{part_id}" → Section}` dict; populated when a "Notes to Part N" heading is detected; used to prevent duplicate notes sections

**Key Methods:**
| Method | Purpose |
|---|---|
| `parse(datalab_result)` | Main entry; stores `_page_objects`, calls `_flatten_blocks()` then `_build_hierarchy()` |
| `_flatten_blocks(datalab_result)` | Produces flat ordered block list from Datalab pages |
| `_build_hierarchy(blocks)` | Builds Chapter→Section→Clause tree; contains nested `add_text()` helper |
| `_find_figure_caption(siblings, fig_idx, alt_text)` | 4-step bidirectional caption search |
| `_flatten_legacy(datalab_result)` | Fallback for old Datalab format or markdown-only responses |
| `_detect_title(blocks)` | Returns first h1 heading text, or `"Building Code Document"` |
| `_parse_part_heading(text)` | Parses Part number and title from h1 text; returns `("FRONT-N", text)` for non-Part h1 headings |
| `_make_section(number, title, page, chapter)` | Creates Section and appends to chapter; deduplicates by `SEC-ID`; longer title wins on collision. Non-numeric section names get chapter-prefixed IDs (e.g. `SEC-CH-FRONT-0-Preface`) to prevent cross-chapter collisions |
| `_make_clause(number, title, page, section)` | Creates Clause, appends to section, registers in `_clause_index` |
| `_clause_id_for(number)` | Returns `CL-{number}` for numbered clauses; `CL-AUTO-{n}` for unnumbered |
| `_note_clause_id_for(note_number)` | Returns `CL-NOTE-{safe}` for note clauses; replaces `.`, `(`, `)` with `-`. Empty number → `CL-NOTE-AUTO-{n}` |
| `_make_note_clause(note_number, title, page, notes_section)` | Creates (or returns existing) Clause under a NotesSection; registers in `_clause_index` |
| `_resolve_hier_target(section_hierarchy, chapters, current_section)` | Resolves Datalab `section_hierarchy` dict to the containing Clause; walks `/page/{idx}/{type}/{child}` paths via `_page_objects` |
| `_remove_empty_clauses(chapters)` | Drops clauses with no content, figures, tables, or equations |
| `_merge_continued_tables(chapters)` | Merges cross-page `(continued)` table fragments; applies cross-page rowspan carry |
| `to_dict(document)` | Thin wrapper — calls `asdict(document)` to return JSON-serializable dict |

**`_flatten_blocks()`** produces flat ordered block list from Datalab pages:
- `SectionHeader` h1-h6 → heading entry; **h0 = untagged SectionHeader** (level returned from `parse_heading`)
- `ListGroup` → sub-clause lines via `listgroup_to_lines()`
- `Equation` → one entry **per `<math>` tag** via `extract_math()` (list); falls back to `strip_html()` if no math tags
- `Text` with `<math>` → marked `has_inline_math=True`, raw HTML preserved for `inline_math_to_markdown()`
- `Figure`/`Picture` → bidirectional caption via `_find_figure_caption()`; decorative images skipped (see below)
- `Caption` → math-aware: uses `inline_math_to_markdown()` if `<math>` present, else `strip_html()`; buffered for next table
- `PageHeader`/`PageFooter`/`TableOfContents`/`Footnote` → skipped

**Decorative image filtering — two stages with different keyword sets:**

In `_flatten_blocks`: skips Figure/Picture blocks where `alt_text.lower()` is an **exact match** for any of: `"horizontal line"`, `"vertical line"`, `"divider"`, `"line"`, `"rule"`, `"separator"`. No length check.

In `_build_hierarchy`: skips figure blocks where alt text is **< 60 characters** AND the text starts with or exactly matches one of: `"horizontal line"`, `"vertical line"`, `"divider"`, `"separator"`, `"solid black line"`, `"decorative"`. The figure counter is decremented when a decorative image is skipped in either stage.

**`_find_figure_caption()` — 4-step search:**
1. Check block immediately **before** — if `Caption`, use it
2. Check block immediately **after** — if `Caption`, use it
3. Check block after for `SectionHeader` matching `"Notes to Figure X"` pattern
4. Fallback: extract figure number from alt text via `RE_FIGURE_NUM`

**`_build_hierarchy()` heading rules:**

**Priority 5 — Notes to Part N** (checked after Division/Preface/CF/Appendix priorities, before mode-specific handling):
- Matched by `RE_NOTES_PART` when `has_hr=True` and `mode in ("normal", "init")` and `current_division` is set
- Finds or creates a `Section` with `id="SEC-NOTES-{target_part.id}"`, `number=""`, appended to `target_part.sections[]`
- Sets `current_notes_section`, `current_note_clause = None`, `current_section = current_notes_section`
- All subsequent headings and text blocks route to notes-mode handlers until a new Part/Division/Appendix heading resets state

**Notes-mode heading handler** (when `current_notes_section is not None` and no Part match):
- Heading matches `RE_NOTE_CLAUSE` (starts with `A-...`) → creates a new note Clause via `_make_note_clause()`; sets `current_note_clause` and `current_clause`
- Heading does not match `RE_NOTE_CLAUSE` → appended as `**bold text**` ContentItem to `current_note_clause`

**Notes-mode text handler** (when `current_notes_section is not None`):
- First line matches `RE_NOTE_CLAUSE` → creates new note Clause; remainder of the text block attached as content
- First line does not match → continuation text appended to `current_note_clause`

**State reset for notes mode** — `current_notes_section` and `current_note_clause` are set to `None` when:
- A new Division heading is encountered
- A new Part heading (`m_part`) is encountered
- An Appendix heading is encountered

- h0 → untagged SectionHeader (1275 in full BCBC 2024):
  - `RE_PART` match → new Chapter with duplicate guard (longer title wins)
  - `RE_SENTENCE` (4-part) match + current_section → new Clause
  - `RE_ARTICLE` (3-part) match + current_section → new Clause
  - `RE_SECTION` (2-part) match + current_chapter → new Section via `_make_section()`
  - plain text + current_section → unnumbered Clause
  - plain text + current_clause → bold text item appended to current clause
- h1 → Part heading if `RE_SECTION` does NOT match (creates new Chapter via `_parse_part_heading()`); if `RE_SECTION` matches and current_chapter exists → new Section (mislabeled h1)
- h2 → `RE_PART` match → new Chapter with duplicate guard; `RE_SECTION` match → new Section; else orphan (skipped)
- h3 → `RE_PART` match → new Chapter with duplicate guard; `RE_ARTICLE` match → new Section via `_make_section()`; else plain title → unnumbered clause
- h4 → check 4-part (`RE_SENTENCE`) **before** 3-part (`RE_ARTICLE`); both create Clauses; plain title → unnumbered clause
- h5 → check `RE_SENTENCE` first, then `RE_ARTICLE` — if matched, create a **numbered** Clause; else create `CL-AUTO-N` (Notes to Table/Figure headings, Appendix entries)
- h6 → if `current_clause` exists → append `**text**` as bold text item in content; else if `current_section` → check `RE_SENTENCE` / `RE_ARTICLE` first (numbered clause), else unnumbered clause

**Duplicate guard pattern** (used in h0, h1, h2, h3 Part handlers):
```python
existing_ch = next((ch for ch in chapters if ch.id == f"CH-{part_num}"), None)
if existing_ch:
    current_chapter = existing_ch
    if part_title and len(part_title) > len(existing_ch.title):
        existing_ch.title = part_title  # longer title wins
else:
    current_chapter = Chapter(id=f"CH-{part_num}", ...)
    chapters.append(current_chapter)
```

**`section_hierarchy` integration** — Every Table, Figure, Picture, and Equation block in Datalab output contains a `section_hierarchy` field mapping depth levels to block IDs in the format `/page/{0-indexed-page}/{blocktype}/{children-index}`. The equation, figure, and table handlers in `_build_hierarchy()` all call `_resolve_hier_target()` when `current_clause` is None:
```python
target = current_clause or self._resolve_hier_target(
    block.get("raw", {}).get("section_hierarchy", {}),
    chapters, current_section
)
```
This recovers content that Datalab assigns between heading blocks (no active clause at parse time), recovering ~40 additional tables and ~7 additional equations for the full BCBC 2024.

**`_resolve_hier_target()` algorithm:**
- Iterates `section_hierarchy` keys in descending depth order
- Each value is a `/page/{idx}/{type}/{child_idx}` path resolved via `self._page_objects[page_idx]['children'][block_idx]`
- Gets `heading_text` from the referenced block's `html`
- Matches against `RE_SENTENCE` → looks up `CL-{num}` in `_clause_index`; if missing, creates new clause in the inferred parent section
- Matches against `RE_ARTICLE` → finds matching section and returns its last clause
- Falls back to `current_section.clauses[-1]` if all paths fail

**Text block auto-detection** (in addition to heading-based hierarchy):
Plain `Text` blocks whose first line matches a structural number pattern are promoted:
- 4-part number → new Clause (guarded: skipped if that `CL-ID` already exists)
- 3-part number → new Section via `_make_section()` (guarded: skipped if that `SEC-ID` already exists, text added to current clause instead)

**Orphaned figure handling:** When a `figure` block resolves no target via `current_clause` OR `_resolve_hier_target()`, a minimal holder clause is created and appended to `current_section`.

**`add_text()` nested helper** (defined inside `_build_hierarchy()`):
If `has_inline_math`, runs `inline_math_to_markdown()` on raw HTML first; then splits by lines; detects sub-clause markers `(a)`, `a)`, `i.` etc.; creates `ContentItem(type="text")` or `ContentItem(type="sub_clause")`.

**Post-processing:**
- `_remove_empty_clauses()` — drops clauses with no content, figures, tables, or equations
- `_merge_continued_tables()` — merges cross-page `(continued)` table fragments into base table; applies cross-page rowspan carry (sandwich detection for 2-col use/load tables)

**`parse_table_html()` — special header collapse rules:**
- **Final-row sub-label skip**: In the column-name collapse loop, when `col == 0` AND `row_i == n_rows - 1` AND the label is ≤4 chars AND matches `^[0-9A-Z]+$` AND the column already has a longer label, the label is skipped. Only applies to col 0 — data columns always keep their final-row labels.
- **Spanning-rows last-row exception**: The spanning subheader detection skips `row_i == n_rows - 1`. The last header row is never treated as a spanning subheader — it is the primary data descriptor and must appear in all columns.

**`_make_section()` — non-numeric section ID uniqueness:**
When `number` starts with a digit (e.g. `"4.1"`), the standard `SEC-4-1` id is used. When `number` is non-numeric (e.g. `"Preface"`), the id is prefixed with the chapter id: `SEC-{chapter.id}-{safe_name}` (e.g. `SEC-CH-FRONT-0-Preface`). This prevents all 35 chapters from sharing a single `SEC-Preface` id when orphaned-content rescue fires.

### Regex Patterns
```python
RE_PART      = r'^Part\s*(\d+)\s*(.*)'         # re.IGNORECASE
RE_SECTION   = r'^(?:Section\s+)?(\d+\.\d+)\.?\s*(.*)'   # re.IGNORECASE
RE_ARTICLE   = r'^(\d+\.\d+\.\d+)\.?\s*(.*)'
RE_SENTENCE  = r'^(\d+\.\d+\.\d+\.\d+)\.?\s*(.*)'        # checked before RE_ARTICLE
RE_SUBCLAUSE = r'^\s*(\([a-z]+\)|[a-z]\)|[ivxlcdm]+\.)\s+(.+)'  # re.IGNORECASE
RE_LEGAL_MARKER = r'^\s*(\([a-z]+\)|[ivx]{2,8}\)|[a-z]\))\s+(.*)'  # re.DOTALL|re.IGNORECASE — used in _process_article_text(); [ivx]{2,8} branch catches multi-char roman numerals like ii), iii), iv) at line start
RE_FIGURE_NUM = r'Figure\s+([\d\.]+[\w\.\-]*)'  # caption fallback from alt text
RE_NOTES_PART = r'^Notes\s+to\s+Part\s*(\d+)\s*(.*)'     # re.IGNORECASE — Priority 5 heading
RE_NOTE_CLAUSE = r'^(A-(?:Table\s+)?[\d]+(?:\.[\d]+)*\.?(?:\(\d+\))?\.?)\s+(.*)'  # re.DOTALL|re.IGNORECASE — note clause number
```

### Public Entry Point
```python
parse_datalab_output(datalab_result, source_pdf="unknown.pdf",
                     figures_dir="storage/figures") -> dict
```
Creates a `StructureParser`, calls `parse()`, then `to_dict()` → returns JSON-serializable document tree.

---

## Reference Linker (`parser/reference_linker.py`)

**Standard cross-references** → `clause.references[]`:
- Kinds: `Sentence`, `Article`, `Subsection`, `Section`, `Clause`, `Table`, `Figure`
- `Subsection` kind maps to `SUBSEC-...` first; if not in id_index falls back to `SEC-...`, then `ART-...`, then `CL-...` — **never generates `SEC-*` as the primary target for a Subsection reference**
- `Section` kind maps to `SEC-...` first; if not in id_index, falls back to `ART-...` then `CL-...`
- Sentence/Article/Clause maps to `CL-...`; if not in id_index, falls back via `title_num_index` to the actual `CL-AUTO-N` id for clauses whose number is only in their title
- Table: type-guarded lookup — only resolves against `TBL-*` nodes; normalized caption match, then fallback ID
- Figure: type-guarded lookup — only resolves against `FIG-*` nodes; exact `reference_key` tried first, then fuzzy normalization fallback; never collides with Table refs
- `resolved: false` for external-PDF targets

**Appendix note references** → `clause.note_refs[]` — pattern: `See Note A-<identifier>`:
- `target_ids` is a **list** (can resolve to multiple clauses)
- **Note index now covers three clause types:**
  - `CL-NOTE-*` clauses — indexed by their `number` field (e.g. `A-4.1.3.2.(2)` → `CL-NOTE-A-4-1-3-2--2-`)
  - `CL-AUTO-*` clauses — indexed by clause title if it starts with `A-` (legacy path)
  - Embedded text items — first line starting with `A-` inside any CL-AUTO clause
- Fallback: strip sentence sub-number and retry (e.g. `A-4.1.3.2.(2)` → `A-4.1.3.2`)
- `resolved: false` for external appendix notes (different PDF)
- **`RE_NOTE` and `RE_A_TITLE` patterns** use `\d+(?:\.\d+)*` (not `[\d\.]+`) so that sub-note identifiers like `A-4.1.6.16.(6)` are captured correctly.
- Note resolution rate improved to **99.8%** (920/922) after adding `CL-NOTE-*` indexing.

**Key functions:**
| Function | Purpose |
|---|---|
| `build_id_index(document_dict)` | Flat `{id→node}` lookup + `_cap_`-prefixed caption keys for tables/figures |
| `build_title_number_index(document_dict)` | Secondary lookup: `CL-X-X-X-X → CL-AUTO-N` for clauses whose number is only in their title (h5/h6 headings that were previously always assigned CL-AUTO) |
| `build_note_index(document_dict)` | Note key → `[clause_id, ...]` lookup; two-pass (titles + embedded text) |
| `_normalize_ref(s)` | Strips dots/hyphens for fuzzy caption matching; handles PDF typos |
| `_ref_to_id(ref, kind, id_index, title_num_index=None)` | Converts reference string to node ID; uses title_num_index fallback for Sentence/Article/Clause; uses CL- fallback for Subsection/Section |
| `_extract_refs_from_text(text)` | Scans text for all standard reference patterns |
| `_extract_notes_from_text(text)` | Scans text for all `(See Note A-...)` patterns |
| `_resolve_note(note_ref, note_index)` | Resolves note ref to list of clause IDs; exact then base match |
| `link_references(document_dict)` | Main entry; populates `references[]` and `note_refs[]` on all clauses |

---

## AI Enhancer (`parser/ai_enhancer.py`)

Claude model: `claude-sonnet-4-20250514`

| Function | Purpose | Max tokens |
|---|---|---|
| `get_claude_client()` | Creates `anthropic.Anthropic()` client; raises `EnvironmentError` if key missing | — |
| `ask_claude(prompt)` | Base call | 1024 |
| `label_table_columns(headers, rows)` | Semantic column labels → `column_semantics[]` | 400 |
| `classify_block(text, ctx_before, ctx_after)` | Classify as clause/continuation/paragraph/list_item (**not called by pipeline**) | 200 |
| `should_join_fragments(end, start)` | Detect cross-page list continuation (**not called by pipeline**) | 10 |
| `resolve_ambiguous_reference(ref, clause_text, ids)` | Resolve "see above table"-style refs (**not called by pipeline**) | 100 |
| `enhance_document(doc, use_ai_for_tables)` | Main entry; walks all tables, adds `column_semantics[]` | — |

All functions strip markdown fences from Claude responses before JSON parsing; fall back to sensible defaults on parse errors.

---

## FastAPI Endpoints (`api/main.py`, port 8000)

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check → `{"status": "ok", "message": "..."}` |
| GET | `/document` | Full document tree |
| GET | `/document/summary` | Lightweight nav tree (chapters + section clause counts, no clause content) |
| GET | `/section/{section_id}` | Single section with clauses |
| GET | `/clause/{clause_id}` | Single clause with `_breadcrumb` context |
| GET | `/search?q=term` | Full-text search (caps at 50 results); snippet = 60 chars before + 100 after match |
| GET | `/references/{node_id}` | Reverse lookup: what clauses reference this node |

**CORS allows `http://localhost:8501` and `http://127.0.0.1:8501`** (Streamlit viewer).

**Caching:** `_document_cache` and `_search_index_cache` as module globals — loaded on first request.

---

## Search Index (`storage/document_store.py`)

`build_search_index()` returns per-clause entries with:

| Field | Source |
|---|---|
| `id`, `type`, `number`, `title` | Clause fields |
| `text` | Concatenation of all content[] items: text/sub_clause `value` + equation `latex` + figure `caption` (or `alt_text` ≤120 chars) + table `value` (caption) |
| `snippet` | First text or sub_clause `value`, truncated to 200 chars |
| `breadcrumb` | `"Chapter N > M.K > L"` |
| `page` | First entry in `page_span` |

---

## Streamlit Viewer (`viewer_streamlit.py`)

Run: `streamlit run viewer_streamlit.py` → opens at http://localhost:8501

Single-page **Extraction Statistics** view. No sidebar mode selector. Sidebar is collapsed by default.

**Sections displayed:**
1. **Top-level counts** — two rows of 4 metrics: Pages, Parts, Sections, Clauses / Equations, Figures, Tables, Flagged
2. **Reference Resolution** — Found / Resolved / Rate metrics + progress bar; appendix note ref summary; table of all unresolved references (clause number, ref text, kind, target)
3. **Per-Part Breakdown** — dataframe with one row per chapter: Sections, Clauses, Equations, Figures, Tables, Flagged counts
4. **Downloads** — download buttons for `structured_document.json` and `raw_{pdf_stem}.json`; collapsible preview of first 200 lines of raw JSON

**Key functions:**
| Function | Purpose |
|---|---|
| `load_document()` | Cached load of `structured_document.json` |
| `load_flags()` | Loads `flagged_issues.json` (used for Flagged metric) |
| `build_clause_list(doc)` | Flat list of all clauses; used for metric aggregation |

**Flagged count** reads from `storage/output/flagged_issues.json`. The file is written externally (previously by the Browse mode flag UI, which has been removed). The count is displayed in the stats but no flag management UI exists in the viewer.

---

## ID Naming Conventions
| Node | Pattern | Example |
|---|---|---|
| Division | `DIV-{letter}` | `DIV-B` |
| Part | `PART-{div}-{n}` | `PART-B-4` |
| Section (numeric) | `SEC-{n}-{m}[-{k}...]` | `SEC-4-1` or `SEC-4-1-6` |
| Section (non-numeric) | `SEC-{parent_id}-{safe_name}` | `SEC-PART-A-1-Preface` |
| Notes Section | `SEC-NOTES-{part_id}` | `SEC-NOTES-PART-B-4` |
| Subsection | `SUBSEC-{n}-{m}-{k}` | `SUBSEC-4-1-6` |
| Article (numbered) | `ART-{n}-{m}-{k}-{j}` | `ART-4-1-1-3` |
| Article (unnumbered) | `ART-AUTO-{n}` | `ART-AUTO-1` |
| Note Article | `ART-NOTE-{A-safe}` | `ART-NOTE-A-4-1-1-3--1-` |
| Sentence | `SENT-{art_safe}-{n}` | `SENT-4-1-1-3-1` |
| Clause (lettered) | `CLAUSE-{art_safe}-{sent_n}-{letter}` | `CLAUSE-4-1-1-3-1-a` |
| Subclause (roman) | `SUBCLAUSE-{clause_id_safe}-{roman}` | `SUBCLAUSE-4-1-1-3-1-a-i` |
| Table | `TBL-{n}` | `TBL-4` |
| Equation | `EQ-{n}` | `EQ-2` |
| Figure | `FIG-{n}` | `FIG-3` |
| Appendix | `APP-{div}-{letter}` | `APP-B-C` |
| Preface Section | `PREF-SEC-{nn}` | `PREF-SEC-01` |
| Conversion Factors Section | `CF-SEC-{nn}` | `CF-SEC-01` |

Periods in article numbers are replaced with hyphens: `4.1.1.3` → `ART-4-1-1-3`.

For note article IDs, `.` `(` `)` are all replaced with `-`: `A-4.1.1.3.(1)` → `ART-NOTE-A-4-1-1-3--1-`.

**Notes Section uniqueness:** Because multiple Divisions each have a Part 1 (e.g. PART-A-1 and PART-B-1), the notes section id is anchored to the full part id (`SEC-NOTES-PART-A-1` vs `SEC-NOTES-PART-B-1`) to prevent collisions in `_section_index`.

**Clause vs Subclause detection:** `_is_roman_numeral(s)` checks if all chars are in `{i, v, x}`. A legal marker is a **Subclause** when it is roman AND a `current_clause_node` already exists; otherwise it is a **Clause** (resets `current_clause_node` for sibling clauses). Before line-by-line parsing, `_normalize_roman_subclause_boundaries(text)` inserts newlines before any inline multi-char roman numeral markers (`ii)`, `iii)`, `iv)` etc.) so sibling subclauses that arrive on the same text run are split into separate parseable boundaries. Only multi-char markers are split; single `i)` is left in place.

---

## Key Patterns & Conventions
- **Env secrets**: always via `load_dotenv()` + `os.getenv()` — never hardcoded
- **Claude model**: `claude-sonnet-4-20250514` (in `ai_enhancer.py`)
- **Inline math**: `<math>` tags in body text → `$...$` notation for `st.markdown()` KaTeX rendering (not block `st.latex()`)
- **Block equations**: each `<math>` tag in an Equation block → separate `EQ-N` ContentItem rendered with `st.latex()`
- **Ingestion cache**: `storage/raw_{pdf_stem}.json` — avoids repeat API charges; bypassed with `--force-extract`
- **Figures dir**: `storage/figures/` — base64 decoded to JPEG, hash-named (not FIG-N.jpg)
- **Figure structured caption**: figures use a structured `caption` dict (not flat string) with fields `raw`, `figure_label`, `figure_number`, `title`; parsed by `_parse_figure_caption()` via `_RE_FIG_CAP_PARSE` regex; applied in `_enrich_figures_in_dict()` post-processing
- **`reference_key` on figures**: canonical string `"Figure {figure_number}"` stored directly on the figure dict; used as the primary lookup key in `build_id_index()` and `_ref_to_id()` for exact figure matching
- **Table caption trailing dot**: `parse_table_caption()` preserves the trailing `"."` in `table_number` and `table_label` when present in source (e.g. `"4.1.5.3."` not `"4.1.5.3"`); title field never starts with `"."`
- **Document cache**: `api/main.py` caches as module globals; loaded on first request
- **Fallback parsing**: `_flatten_legacy()` handles old Datalab format or markdown-only responses
- **h0 headings**: SectionHeader blocks where Datalab assigns no h1–h6 tag (`parse_heading()` returns level=0); in BCBC 2024 these are 1275 article/sentence-level clause headings plus some Part headings — all routed in the h0 handler
- **Heading levels**: h0→clause/section/part (auto-detected), h1→Part or mislabeled section, h2→Part or Section, h3→Part or Section(3-part), h4→Clause (4-part checked first), h5→numbered clause (RE_SENTENCE/RE_ARTICLE checked first) or CL-AUTO, h6→bold text item or numbered/unnumbered clause
- **Duplicate guard on Parts**: all Part heading handlers (h0, h1, h2, h3) check if `CH-{n}` already exists; if so, reuse and update title (longer wins) rather than creating duplicate
- **FRONT-N chapters**: non-Part h1 headings (title pages, preface) get `CH-FRONT-{counter}` IDs to avoid collisions with actual Parts
- **`_make_section()` deduplication**: returns existing section if `SEC-ID` already present in chapter; longer title wins on collision; non-numeric names get `SEC-{chapter_id}-{safe}` to prevent cross-chapter collisions
- **`_clause_index` fast lookup**: populated by `_make_clause()`; enables `_resolve_hier_target()` to attach orphaned content without iterating the full chapter tree
- **`section_hierarchy` recovery**: Datalab provides `/page/{idx}/{type}/{child}` paths on every Table/Figure/Equation block; used to recover content orphaned between headings (no active clause at parse time)
- **Text block promotion**: text blocks starting with a structural number can auto-promote to section/clause; duplicate-ID guards prevent re-creation
- **Bidirectional caption search**: figure captions looked up before, after, and via "Notes to Figure" heading
- **Table merging**: cross-page `(continued)` fragments merged into base table; cross-page rowspan carry via sandwich detection
- **Rowspan/colspan parsing**: multi-row `<thead>` with label grid collapsing; `<tbody>` rowspan carry dict; bbox-based carry for Datalab-missing rowspan attrs
- **Decorative image filtering**: two-stage with different keyword sets — `_flatten_blocks` uses exact-match; `_build_hierarchy` uses <60 char check + starts_with/exact; figure counter decremented on skip
- **Orphaned figure handling**: tries `_resolve_hier_target()` first; falls back to creating a minimal holder clause
- **Storage is file-based** — `document_store.py` noted as swap candidate for PostgreSQL/SQLite
- **Reference normalization**: dots/hyphens stripped for fuzzy caption matching (handles PDF typos)
- **Note index three-source**: `build_note_index()` now indexes (1) `CL-NOTE-*` clause numbers (primary — all A-numbered note clauses have dedicated IDs), (2) `CL-AUTO-*` clause titles that start with `A-` (legacy path), and (3) embedded text items in CL-AUTO clauses whose first line starts with `A-`
- **Note ref regex**: `RE_NOTE` and `RE_A_TITLE` use `\d+(?:\.\d+)*` (not `[\d\.]+`) so sub-note identifiers such as `A-4.1.6.16.(6)` are captured fully
- **Title-number index**: `build_title_number_index()` maps derived `CL-X-X-X-X` → actual `CL-AUTO-N` for clauses whose number appears only in their title; used as fallback in `_ref_to_id()` to resolve references that previously failed because the clause had a CL-AUTO id
- **Notes sections**: "Notes to Part N" headings (with `<hr/>`) become `SEC-NOTES-{part_id}` Sections inside `part.sections[]` at the same level as regular code sections; no subsection nesting; clauses hold `CL-NOTE-*` IDs
- **Notes state tracking**: `_build_hierarchy()` tracks `current_notes_section` and `current_note_clause`; state is reset on Division/Part/Appendix heading transitions; all non-Part headings and text blocks while in notes mode route to the notes handlers
- **Note clause ID formula**: `_note_clause_id_for()` replaces `.`, `(`, `)` with `-` in the A-number; e.g. `A-4.1.1.3.(1)` → `CL-NOTE-A-4-1-1-3--1-`
- **`_notes_section_index`**: dict `{sec_id → Section}` prevents duplicate notes sections when "Notes to Part N" heading is seen more than once
- **Subsection prefix rule**: `_ref_to_id()` for `Subsection` kind always resolves to `SUBSEC-*` first; `SEC-*` is the fallback only when no `SUBSEC-*` node exists — never the primary target. This fixed all 416 previously-wrong `SEC-*` subsection refs.
- **SEC→CL fallback**: `_ref_to_id()` for `Section` kind tries `SEC-` first; if not in id_index, tries `ART-` then `CL-` — handles cases where a 3-part numbered heading was parsed as an Article/Clause rather than a Section
- **Deduplication**: reference linker tracks `(kind, ref)` tuples per clause; note linker tracks `note_ref` per clause
- **`note_refs[]` is dynamic**: not part of the `Clause` dataclass — added to the dict by `reference_linker.link_references()`; `target_ids` now resolve to `CL-NOTE-*` IDs (previously resolved to `CL-AUTO-*`)
- **Real Parts metric**: `sum(1 for ch in chapters if ch.get("number","").isdigit())` — excludes FRONT-N chapters from the "Parts" count in Stats
- **Unused AI functions**: `classify_block()`, `should_join_fragments()`, and `resolve_ambiguous_reference()` in `ai_enhancer.py` are defined but not called anywhere in the current pipeline — available for future use

---

## Extraction Results — Full BCBC 2024 (`bcbc_2024_web_version_revision2.pdf`)
| Metric | Value |
|---|---|
| Pages | 1906 |
| Divisions | 3 (A, B, C) |
| Parts | 15 |
| Sections | 114 |
| Subsections | 445 |
| Articles | 3,118 (includes note articles) |
| Sentences | 5,664 |
| Clauses (lettered) | 4,201 |
| Subclauses (roman) | 1,078 |
| Tables | 469 |
| Figures | 212 |
| Equations | 110 |
| Reference resolution | 97.4% (2,867/2,945) |
| Note resolution | 99.8% (920/922) |

Unresolved cross-references (~15.3%) point to other volumes in the BCBC series not in this PDF. Only 2 note refs are unresolved (genuine external appendix notes).

**Parts with Notes Sections:**
PART-A-1, PART-A-2, PART-A-3, PART-B-1, PART-B-3, PART-B-4, PART-B-5, PART-B-6, PART-B-8, PART-B-9, PART-B-10, PART-C-2 — note articles stored with `ART-NOTE-` prefix in `section.articles`.

---

## How to Run
```bash
# 1. Process a PDF
python main.py bcbc_2024_web_version_revision2.pdf
python main.py bcbc_2024_web_version_revision2.pdf --force-extract  # skip cache, re-call Datalab API
python main.py bcbc_2024_web_version_revision2.pdf --ai             # with Claude table enhancement

# 2. Start API
uvicorn api.main:app --reload --port 8000

# 3. Start Streamlit viewer (Extraction Statistics)
streamlit run viewer_streamlit.py
```

---

## Potential Feature Areas (for future prompts)
- Document browsing UI — Browse mode (section-by-section navigation with prev/next) and Search mode (full-text client-side search) were previously implemented in `viewer_streamlit.py` but removed to simplify the viewer; could be re-added or rebuilt as a React/Next.js frontend
- React/Next.js frontend (CORS currently configured for Streamlit port 8501 — update for port 3000 if adding React)
- Inline reference rendering in clause text (refs are stored in `references[]` per clause but no UI currently renders them as hyperlinks)
- Export to PDF/Word/CSV
- Multi-document support (currently single document per pipeline run)
- Database backend (PostgreSQL/SQLite replacing JSON file storage)
- Authentication for the API
- Annotation/comment system on clauses
- Diff view between two versions of a building code
- Clause comparison across documents
- AI-powered Q&A over the document (RAG)
- Wire up unused AI pipeline functions (`classify_block`, `should_join_fragments`, `resolve_ambiguous_reference`) or remove them
- Remove unused `pdfplumber` and `pymupdf` dependencies from `requirements.txt`
- Improve `_resolve_hier_target()` to handle deeper nesting and edge cases where the hierarchy path points to a non-heading block type
- Further increase reference resolution beyond 97.4% — remaining ~78 unresolved refs are likely genuine external-volume references pointing to other BCBC volumes not in this PDF
