# Frontend Schema Briefing — BCBC 2024 Structured Document

**Source file:** `storage/output/structured_document.json` (~19 MB)
**Document:** British Columbia Building Code 2024 (1906 pages)

---

## 1. Overview

The JSON document is a fully parsed, hierarchically structured representation of the BCBC 2024 PDF. It organizes the code into **Divisions → Parts → Sections → Subsections → Clauses**, with each clause carrying its content inline as an ordered array of typed items (text, equations, figures, tables, sub-clauses). Cross-references and appendix note references are resolved and embedded per-clause.

Each Part that contains a "Notes to Part" section in the PDF now also includes a dedicated **Notes Section** (`SEC-NOTES-*`) at the same level as regular code sections. Notes sections hold note clauses (`CL-NOTE-*`) directly — no subsection nesting.

### Scale (actual counts from file)

| Entity | Count |
|---|---|
| Divisions | 3 |
| Parts | 15 |
| Regular Sections | 102 |
| Notes Sections | 12 |
| Subsections | 445 |
| Regular Clauses | 2,419 |
| Note Clauses | 699 |
| Tables | 469 |
| Figures | 212 |
| Equations | 110 |
| Cross-references | 2,945 |
| Appendix note refs | 922 (99.8% resolved) |

---

## 2. Top-Level Document Object

```json
{
  "title": "British Columbia BUILDING CODE 2024",
  "source_pdf": "bcbc_2024_web_version_revision2.pdf",
  "total_pages": 1906,
  "preface": { ... },
  "divisions": [ ... ],
  "conversion_factors": { ... },
  "_stats": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `title` | `string` | Document title |
| `source_pdf` | `string` | Original PDF filename |
| `total_pages` | `number` | Total page count |
| `preface` | `Preface` | Front-matter preface object |
| `divisions` | `Division[]` | Main content — array of 3 divisions (A, B, C) |
| `conversion_factors` | `ConversionFactors` | Standalone conversion factors section |
| `_stats` | `Stats` | Reference resolution statistics |

---

## 3. Schema

### 3.1 Stats

```json
"_stats": {
  "total_references": 2945,
  "resolved_references": 2495,
  "resolution_rate_pct": 84.7,
  "total_note_refs": 922,
  "resolved_note_refs": 920,
  "note_resolution_rate_pct": 99.8
}
```

| Field | Type |
|---|---|
| `total_references` | `number` |
| `resolved_references` | `number` |
| `resolution_rate_pct` | `number` |
| `total_note_refs` | `number` |
| `resolved_note_refs` | `number` |
| `note_resolution_rate_pct` | `number` |

---

### 3.2 Preface

```json
"preface": {
  "id": "PREFACE",
  "title": "Preface",
  "sections": [ PrefaceSection ],
  "page_span": [11]
}
```

| Field | Type |
|---|---|
| `id` | `string` — always `"PREFACE"` |
| `title` | `string` |
| `sections` | `PrefaceSection[]` |
| `page_span` | `number[]` |

**PrefaceSection** — has its own `content[]` array (same ContentItem schema as Clause, see §3.8), no `clauses[]`:

```json
{
  "id": "PREF-SEC-01",
  "number": "",
  "title": "Preface Content",
  "content": [ ContentItem ],
  "subsections": [],
  "page_span": [11]
}
```

---

### 3.3 ConversionFactors

```json
"conversion_factors": {
  "id": "CONV-FACTORS",
  "title": "Conversion Factors",
  "sections": [ ConversionSection ],
  "page_span": [...]
}
```

**ConversionSection** — contains `content[]` and `tables[]` directly (no `clauses[]`):

```json
{
  "id": "...",
  "number": "",
  "title": "...",
  "content": [ ContentItem ],
  "tables": [ Table ],
  "figures": [ Figure ],
  "page_span": [...]
}
```

---

### 3.4 Division

```json
{
  "id": "DIV-B",
  "number": "B",
  "title": "Division B",
  "parts": [ Part ],
  "appendices": [ Appendix ],
  "page_span": [120, 121, ...]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"DIV-A"` / `"DIV-B"` / `"DIV-C"` |
| `number` | `string` | `"A"` / `"B"` / `"C"` |
| `title` | `string` | e.g. `"Division B"` |
| `parts` | `Part[]` | The Parts within this division |
| `appendices` | `Appendix[]` | Optional appendices (only DIV-B has 2) |
| `page_span` | `number[]` | All page numbers covered |

---

### 3.5 Part

```json
{
  "id": "PART-B-4",
  "number": "4",
  "title": "Structural Design",
  "sections": [ Section ],
  "page_span": [490, 491, ...]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"PART-{div}-{n}"` e.g. `"PART-B-4"` |
| `number` | `string` | Part number string |
| `title` | `string` | Part title |
| `sections` | `Section[]` |  |
| `page_span` | `number[]` |  |

---

### 3.6 Section

```json
{
  "id": "SEC-4-1",
  "number": "4.1",
  "title": "Structural Loads and Procedures",
  "subsections": [ Subsection ],
  "clauses": [ Clause ],
  "page_span": [490, 491, ...]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | `"SEC-{n}-{m}"` |
| `number` | `string` | e.g. `"4.1"` |
| `title` | `string` | |
| `subsections` | `Subsection[]` | Usually populated; `clauses[]` may be empty |
| `clauses` | `Clause[]` | Direct clauses (uncommon — most are in subsections) |
| `page_span` | `number[]` | |

> **Key design note:** Most clauses live under **Subsections**, not Sections directly. Always check both `section.clauses[]` and `section.subsections[].clauses[]` when traversing.

---

### 3.6a NotesSection — Part Notes (Special Section Type)

Parts that include a "Notes to Part" segment in the PDF expose a dedicated notes section at the **same level** as regular numbered sections inside `part.sections[]`. It holds note clauses directly — no subsection nesting.

```json
{
  "id": "SEC-NOTES-PART-B-4",
  "number": "",
  "title": "Notes to Part 4 Structural Design",
  "subsections": [],
  "clauses": [ NoteClause ],
  "page_span": [627, 628, ...]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | `"SEC-NOTES-{part_id}"` e.g. `"SEC-NOTES-PART-B-4"` |
| `number` | `string` | Always `""` (empty) |
| `title` | `string` | `"Notes to Part {n} {Part Title}"` |
| `subsections` | `Subsection[]` | Always empty `[]` |
| `clauses` | `NoteClause[]` | Note clauses held directly (no subsection nesting) |
| `page_span` | `number[]` | Pages covered by the notes segment |

**Which Parts have a NotesSection:**

| Part | Notes Section ID | Note Clauses |
|---|---|---|
| PART-A-1 (Compliance) | `SEC-NOTES-PART-A-1` | 9 |
| PART-A-2 (Objectives) | `SEC-NOTES-PART-A-2` | 2 |
| PART-A-3 (Functional Statements) | `SEC-NOTES-PART-A-3` | 1 |
| PART-B-1 (General) | `SEC-NOTES-PART-B-1` | 4 |
| PART-B-3 (Fire Protection) | `SEC-NOTES-PART-B-3` | 200 |
| PART-B-4 (Structural Design) | `SEC-NOTES-PART-B-4` | 114 |
| PART-B-5 (Environmental Separation) | `SEC-NOTES-PART-B-5` | 51 |
| PART-B-6 (HVAC) | `SEC-NOTES-PART-B-6` | 23 |
| PART-B-8 (Construction Safety) | `SEC-NOTES-PART-B-8` | 1 |
| PART-B-9 (Housing) | `SEC-NOTES-PART-B-9` | 281 |
| PART-B-10 (Energy Efficiency) | `SEC-NOTES-PART-B-10` | 6 |
| PART-C-2 (Administrative Provisions) | `SEC-NOTES-PART-C-2` | 7 |

**NoteClause** — same shape as a regular `Clause` (§3.8) but with an `A-`-prefixed number and a `CL-NOTE-` id:

```json
{
  "id": "CL-NOTE-A-4-1-1-3--1-",
  "number": "A-4.1.1.3.(1)",
  "title": "Structural Integrity",
  "content": [ ContentItem ],
  "tables": [],
  "figures": [],
  "equations": [],
  "references": [],
  "note_refs": [],
  "page_span": [627]
}
```

> **Identification:** Detect a NoteClause by `id.startsWith("CL-NOTE-")` or `number.startsWith("A-")`. Detect a NotesSection by `id.startsWith("SEC-NOTES-")`.

---

### 3.7 Subsection

```json
{
  "id": "SUBSEC-4-1-6",
  "number": "4.1.6",
  "title": "Wind Load",
  "clauses": [ Clause ],
  "page_span": [510, 511, ...]
}
```

| Field | Type |
|---|---|
| `id` | `string` — `"SUBSEC-{n}-{m}-{k}"` |
| `number` | `string` |
| `title` | `string` |
| `clauses` | `Clause[]` |
| `page_span` | `number[]` |

---

### 3.8 Clause — The Core Content Node

```json
{
  "id": "CL-4-1-6-5",
  "number": "4.1.6.5",
  "title": "Snow Load on Lower Roofs",
  "content": [ ContentItem ],
  "tables": [ Table ],
  "figures": [ Figure ],
  "equations": [ Equation ],
  "references": [ Reference ],
  "note_refs": [ NoteRef ],
  "page_span": [530, 531, 532]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"CL-{n}-{m}-{k}-{j}"` or `"CL-AUTO-{n}"` for unnumbered |
| `number` | `string` | Dotted number e.g. `"4.1.6.5"` |
| `title` | `string` | Clause heading |
| `content` | `ContentItem[]` | **Ordered** inline content (see §3.8.1) |
| `tables` | `Table[]` | Full table data (see §3.9) |
| `figures` | `Figure[]` | Figure metadata and image paths (see §3.10) |
| `equations` | `Equation[]` | Block equations with LaTeX (see §3.11) |
| `references` | `Reference[]` | Outgoing cross-references (see §3.12) |
| `note_refs` | `NoteRef[]` | Appendix note references (see §3.13) |
| `page_span` | `number[]` | Page numbers this clause spans |

---

#### 3.8.1 ContentItem — Inline Content

All content items share the same flat shape; fields not applicable to the type will be empty strings.

```typescript
type ContentItemType = "text" | "sub_clause" | "equation" | "figure" | "table";

interface ContentItem {
  type:       ContentItemType;
  value:      string;   // text body, or equation ID (e.g. "EQ-13"), or table caption, or ""
  latex:      string;   // LaTeX string — only for type="equation"
  figure_id:  string;   // e.g. "FIG-56"  — only for type="figure"
  image_key:  string;   // filename hash — only for type="figure"
  image_path: string;   // relative path  — only for type="figure"
  caption:    string;   // figure caption  — only for type="figure"
  alt_text:   string;   // figure alt text — only for type="figure"
  table_id:   string;   // e.g. "TBL-218" — only for type="table"
  marker:     string;   // sub-clause marker e.g. "b)", "(iii)" — only for type="sub_clause"
}
```

**Type-specific usage:**

| type | `value` | Other active fields |
|---|---|---|
| `"text"` | Paragraph text (may contain `$...$` inline math) | — |
| `"sub_clause"` | Sub-clause text | `marker` = label e.g. `"b)"` |
| `"equation"` | Equation ID e.g. `"EQ-13"` | `latex` = full LaTeX string |
| `"figure"` | `""` | `figure_id`, `image_key`, `image_path`, `caption`, `alt_text` |
| `"table"` | Table caption text | `table_id` |

> **Rendering note:** `value` for `"text"` items may contain `$...$` KaTeX inline math. Block equations are in `"equation"` items with the full `latex` string. Both must be rendered mathematically.

---

### 3.9 Table

```json
{
  "id": "TBL-218",
  "caption": "Table 4.1.6.5.-B Parameters for Snow Load Cases...",
  "headers": ["Parameter", "Case I", "Case II", "Case III"],
  "rows": [
    ["\\beta", "1.0", "0.67", "0.67"],
    ["C_a", "...", "...", "..."]
  ],
  "page": 532,
  "column_semantics": ["parameter_name", "case_1_value", "case_2_value", "case_3_value"]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"TBL-{n}"` |
| `caption` | `string` | Full caption including table number |
| `headers` | `string[]` | Column header labels |
| `rows` | `string[][]` | Data rows — each row is an array of cell strings |
| `page` | `number` | Page where the table appears |
| `column_semantics` | `string[]` | AI-generated semantic labels per column (may be empty array if AI enhancement was not run) |

> Cells may contain LaTeX math (backslash notation). Render with KaTeX or MathJax.

---

### 3.10 Figure

```json
{
  "id": "FIG-56",
  "caption": "Figure 4.1.6.5.-B Snow load cases I, II and III...",
  "alt_text": "Figure 4.1.6.5.-B: ROOF PLAN showing three snow load cases...",
  "image_key": "223b363465c3987e97bf7cf0bc1dbe0d_img.jpg",
  "image_path": "storage\\figures\\223b363465c3987e97bf7cf0bc1dbe0d_img.jpg",
  "page": 532
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"FIG-{n}"` |
| `caption` | `string` | Figure caption |
| `alt_text` | `string` | Accessibility description |
| `image_key` | `string` | Filename (hash-based) in `storage/figures/` |
| `image_path` | `string` | Relative path from project root (Windows backslashes) |
| `page` | `number` | Source page |

> **Path note:** `image_path` uses Windows backslashes. Normalize to forward slashes on the frontend or use `image_key` to build the URL via the API.

---

### 3.11 Equation

```json
{
  "id": "EQ-13",
  "latex": "C_{a0} = \\beta \\frac{\\gamma h}{C_b S_s} \\text{ and}",
  "page": 531
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"EQ-{n}"` |
| `latex` | `string` | LaTeX math string (without `$` delimiters) |
| `page` | `number` | Source page |

> Render with `\[ ... \]` block display (MathJax) or `\displaystyle` (KaTeX).

---

### 3.12 Reference

```json
{
  "text": "Table 4.1.6.5.-A",
  "kind": "Table",
  "target_id": "TBL-217",
  "resolved": true
}
```

| Field | Type | Description |
|---|---|---|
| `text` | `string` | Original reference text as it appeared in the PDF |
| `kind` | `string` | One of: `"Sentence"`, `"Article"`, `"Subsection"`, `"Section"`, `"Clause"`, `"Table"`, `"Figure"` |
| `target_id` | `string` | ID of the referenced node (e.g. `"CL-4-1-6-5"`, `"TBL-217"`, `"FIG-3"`) |
| `resolved` | `boolean` | `true` if target exists in this document; `false` if it points to an external volume |

> Unresolved references (~15%) point to other BCBC volumes not in this PDF. Only render links when `resolved: true`.

---

### 3.13 NoteRef

```json
{
  "raw": "See Note A-1.1.1.1.(3).",
  "note_ref": "A-1.1.1.1.(3).",
  "target_ids": ["CL-AUTO-1"],
  "resolved": true
}
```

| Field | Type | Description |
|---|---|---|
| `raw` | `string` | Full original text including "See Note " |
| `note_ref` | `string` | The extracted note identifier |
| `target_ids` | `string[]` | Array of clause IDs (can resolve to multiple) |
| `resolved` | `boolean` | `true` if all targets exist in this document |

---

### 3.14 Appendix

```json
{
  "id": "APP-B-C",
  "number": "C",
  "title": "Climatic and Seismic Information for Building Design in Canada",
  "sections": [ Section ],
  "page_span": [...]
}
```

| Field | Type |
|---|---|
| `id` | `string` — `"APP-{div}-{letter}"` |
| `number` | `string` |
| `title` | `string` |
| `sections` | `Section[]` |
| `page_span` | `number[]` |

---

## 4. ID Naming Conventions

| Entity | Pattern | Example |
|---|---|---|
| Division | `DIV-{letter}` | `DIV-B` |
| Part | `PART-{div}-{n}` | `PART-B-4` |
| Section | `SEC-{n}-{m}` | `SEC-4-1` |
| Notes Section | `SEC-NOTES-{part_id}` | `SEC-NOTES-PART-B-4` |
| Subsection | `SUBSEC-{n}-{m}-{k}` | `SUBSEC-4-1-6` |
| Clause (numbered) | `CL-{n}-{m}-{k}-{j}` | `CL-4-1-6-5` |
| Clause (unnumbered) | `CL-AUTO-{n}` | `CL-AUTO-153` |
| Note Clause | `CL-NOTE-{A-num}` | `CL-NOTE-A-4-1-1-3--1-` |
| Table | `TBL-{n}` | `TBL-218` |
| Figure | `FIG-{n}` | `FIG-56` |
| Equation | `EQ-{n}` | `EQ-13` |
| Appendix | `APP-{div}-{letter}` | `APP-B-C` |
| Preface section | `PREF-SEC-{nn}` | `PREF-SEC-01` |

> Dots in clause numbers are replaced with hyphens: `4.1.6.5` → `CL-4-1-6-5`.
> For note clauses, `.` `(` `)` are all replaced with `-`: `A-4.1.1.3.(1)` → `CL-NOTE-A-4-1-1-3--1-`.

---

## 5. Document Tree — Full Hierarchy Diagram

```
Document
├── title, source_pdf, total_pages, _stats
│
├── preface
│   └── sections[]
│       ├── id, number, title, page_span
│       ├── content[]  ← ContentItem[]  (same schema as Clause content)
│       └── subsections[]
│
├── divisions[]
│   ├── id, number, title, page_span
│   ├── parts[]
│   │   ├── id, number, title, page_span
│   │   └── sections[]
│   │       ├── [Regular Section]  id="SEC-4-1", number="4.1"
│   │       │   ├── id, number, title, page_span
│   │       │   ├── subsections[]
│   │       │   │   ├── id, number, title, page_span
│   │       │   │   └── clauses[]   ←── PRIMARY CONTENT LOCATION
│   │       │   │       ├── id, number, title, page_span
│   │       │   │       ├── content[]       ← ContentItem[] (ordered)
│   │       │   │       ├── tables[]        ← Table[]
│   │       │   │       ├── figures[]       ← Figure[]
│   │       │   │       ├── equations[]     ← Equation[]
│   │       │   │       ├── references[]    ← Reference[]
│   │       │   │       └── note_refs[]     ← NoteRef[]
│   │       │   └── clauses[]   ←── (direct section clauses, less common)
│   │       └── [Notes Section]  id="SEC-NOTES-PART-B-4", number=""  ← SAME LEVEL as regular sections
│   │           ├── id, number="", title, page_span
│   │           ├── subsections[]  ← always []
│   │           └── clauses[]   ←── NOTE CLAUSES (direct, no subsection nesting)
│   │               ├── id="CL-NOTE-A-4-1-1-3--1-", number="A-4.1.1.3.(1)"
│   │               ├── title, page_span
│   │               ├── content[]       ← ContentItem[] (ordered)
│   │               ├── tables[], figures[], equations[]
│   │               ├── references[]    ← Reference[]
│   │               └── note_refs[]     ← NoteRef[]
│   └── appendices[]
│       ├── id, number, title, page_span
│       └── sections[]  (same structure as Regular Section above)
│
└── conversion_factors
    ├── id, title, page_span
    └── sections[]
        ├── id, number, title, page_span
        ├── content[]   ← ContentItem[]
        └── tables[]    ← Table[]
```

---

## 6. API Endpoints (port 8000)

The FastAPI backend exposes the document for frontend consumption:

| Method | Path | Returns |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/document` | Full document tree (large — ~19 MB) |
| `GET` | `/document/summary` | Lightweight nav tree (chapters + section counts only) |
| `GET` | `/section/{section_id}` | Single section with its clauses |
| `GET` | `/clause/{clause_id}` | Single clause + `_breadcrumb` context |
| `GET` | `/search?q={term}` | Full-text search (max 50 results) |
| `GET` | `/references/{node_id}` | Reverse lookup: which clauses reference this node |

---

## 7. Frontend Rendering Guidance

### Math
- **Inline math** in `text` and `sub_clause` items: delimited by `$...$` → render with KaTeX inline mode.
- **Block equations** in `equation` items: use the `latex` field → render with KaTeX `\displaystyle` or MathJax block mode.
- **Table cells** may also contain LaTeX notation (e.g. Greek letters like `\beta`).

### Images
- Figures are served from `storage/figures/{image_key}`.
- Always use `image_key` to build URLs; `image_path` uses Windows backslashes and is not suitable as-is.
- Always render `alt_text` for accessibility.

### References / Links
- Only render `references[]` entries as clickable links when `resolved: true`.
- `target_id` maps directly to the ID system above — use it to build deep links.
- For `note_refs[]`, `target_ids` is an array — a note may link to multiple clauses.

### Content ordering
- `content[]` is an **ordered** array preserving the original PDF reading sequence. Render items in array order without reordering.
- `tables[]`, `figures[]`, and `equations[]` are detail collections for lookup by ID. The inline `content[]` items of type `"table"` and `"figure"` mark the position of those elements in reading order and reference them by ID.

### Traversal pattern
```
Document → divisions[] → parts[] → sections[] → subsections[] → clauses[]
                                               ↘ clauses[]  (also check here)
```

When traversing `part.sections[]`, a section is a **NotesSection** when `section.id.startsWith("SEC-NOTES-")`. Notes sections hold clauses directly in `section.clauses[]` — skip the subsections loop.

```typescript
for (const section of part.sections) {
  if (section.id.startsWith("SEC-NOTES-")) {
    // Notes section — clauses are direct children
    renderNotesClauses(section.clauses);
  } else {
    // Regular section — clauses are inside subsections
    for (const sub of section.subsections) renderClauses(sub.clauses);
    if (section.clauses.length) renderClauses(section.clauses);
  }
}
```

### Notes Clauses
- A note clause has `id` starting with `"CL-NOTE-"` and `number` starting with `"A-"`.
- Its `content[]`, `tables[]`, `figures[]`, `equations[]`, `references[]`, and `note_refs[]` follow the same schema as regular clauses (§3.8).
- Render notes sections with a distinct visual style (e.g., collapsible panel, different background) to distinguish them from normative code content.
- The `note_refs[]` on regular clauses (e.g. `"See Note A-4.1.1.3.(1)."`) resolve to `target_ids` containing `CL-NOTE-*` IDs — use these to deep-link into the notes section.

### Navigation data
- Use `GET /document/summary` to build a navigation tree without loading all clause content.
- `page_span` on every node allows mapping to original PDF page numbers for a "view in PDF" link.
- Notes sections appear at the end of their Part's `sections[]` array.
