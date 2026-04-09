# Frontend Schema Briefing — BCBC 2024 Structured Document

**Source file:** `storage/output/structured_document.json` (~19.9 MB)
**Document:** British Columbia Building Code 2024 (1906 pages)

---

## 1. Overview

The JSON document is a fully parsed, hierarchically structured representation of the BCBC 2024 PDF. It organizes the code into the full legal hierarchy:

**Divisions → Parts → Sections → Subsections → Articles → Sentences → Clauses → Subclauses**

Each **Article** (a 4-part numbered provision like `4.1.1.3`) contains explicit **Sentence** nodes for numbered items (`1)`, `2)`), which in turn hold **Clause** nodes for lettered items (`(a)`, `(b)`), which hold **Subclause** nodes for roman-numeral items (`(i)`, `(ii)`). This replaces the previous flat `content[]` approach.

Cross-references and appendix note references are resolved and embedded per-article.

Each Part that contains a "Notes to Part" section in the PDF also includes a dedicated **Notes Section** (`SEC-NOTES-*`) at the same level as regular code sections. Notes sections hold note articles (`ART-NOTE-*`) directly — no subsection nesting.

### Scale (actual counts from file)

| Entity | Count |
|---|---|
| Divisions | 3 |
| Parts | 15 |
| Sections | 114 |
| Subsections | 445 |
| Articles | 3,118 |
| Sentences | 5,383 |
| Clauses (lettered) | 3,695 |
| Subclauses (roman) | 111 |
| Tables | 469 |
| Figures | 212 |
| Equations | 110 |
| Cross-references | 2,945 (84.7% resolved) |
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

**PrefaceSection** — has its own `content[]` array (same ContentItem schema as §3.9.1), no `articles[]`:

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

> **Unchanged from previous schema** — Preface hierarchy is not affected by the Article/Sentence/Clause refactor.

---

### 3.3 ConversionFactors

```json
"conversion_factors": {
  "id": "CONVERSION-FACTORS",
  "title": "Conversion Factors",
  "sections": [ ConversionSection ],
  "page_span": [...]
}
```

**ConversionSection** — contains `content[]` and `tables[]` directly (no `articles[]`):

```json
{
  "id": "CF-SEC-01",
  "number": "",
  "title": "...",
  "content": [ ContentItem ],
  "tables": [ Table ],
  "figures": [ Figure ],
  "page_span": [...]
}
```

> **Unchanged from previous schema** — ConversionFactors hierarchy is not affected by the Article/Sentence/Clause refactor.

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
| `sections` | `Section[]` | Regular code sections + optional Notes Section |
| `page_span` | `number[]` | |

---

### 3.6 Section

```json
{
  "id": "SEC-4-1",
  "number": "4.1",
  "title": "Structural Loads and Procedures",
  "subsections": [ Subsection ],
  "articles": [ Article ],
  "page_span": [490, 491, ...]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | `"SEC-{n}-{m}"` |
| `number` | `string` | e.g. `"4.1"` |
| `title` | `string` | |
| `subsections` | `Subsection[]` | Usually populated; `articles[]` may be empty |
| `articles` | `Article[]` | Direct articles (uncommon — most are in subsections) |
| `page_span` | `number[]` | |

> **Key design note:** Most articles live under **Subsections**, not Sections directly. Always check both `section.articles[]` and `section.subsections[].articles[]` when traversing.

---

### 3.6a NotesSection — Part Notes (Special Section Type)

Parts that include a "Notes to Part" segment in the PDF expose a dedicated notes section at the **same level** as regular numbered sections inside `part.sections[]`. It holds note articles directly — no subsection nesting.

```json
{
  "id": "SEC-NOTES-PART-B-4",
  "number": "",
  "title": "Notes to Part 4 Structural Design",
  "subsections": [],
  "articles": [ NoteArticle ],
  "page_span": [627, 628, ...]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | `"SEC-NOTES-{part_id}"` e.g. `"SEC-NOTES-PART-B-4"` |
| `number` | `string` | Always `""` (empty) |
| `title` | `string` | `"Notes to Part {n} {Part Title}"` |
| `subsections` | `Subsection[]` | Always empty `[]` |
| `articles` | `NoteArticle[]` | Note articles held directly (no subsection nesting) |
| `page_span` | `number[]` | Pages covered by the notes segment |

**Which Parts have a NotesSection:**

| Part | Notes Section ID |
|---|---|
| PART-A-1 (Compliance) | `SEC-NOTES-PART-A-1` |
| PART-A-2 (Objectives) | `SEC-NOTES-PART-A-2` |
| PART-A-3 (Functional Statements) | `SEC-NOTES-PART-A-3` |
| PART-B-1 (General) | `SEC-NOTES-PART-B-1` |
| PART-B-3 (Fire Protection) | `SEC-NOTES-PART-B-3` |
| PART-B-4 (Structural Design) | `SEC-NOTES-PART-B-4` |
| PART-B-5 (Environmental Separation) | `SEC-NOTES-PART-B-5` |
| PART-B-6 (HVAC) | `SEC-NOTES-PART-B-6` |
| PART-B-8 (Construction Safety) | `SEC-NOTES-PART-B-8` |
| PART-B-9 (Housing) | `SEC-NOTES-PART-B-9` |
| PART-B-10 (Energy Efficiency) | `SEC-NOTES-PART-B-10` |
| PART-C-2 (Administrative Provisions) | `SEC-NOTES-PART-C-2` |

**NoteArticle** — same outer shape as a regular `Article` (§3.8) but with an `A-`-prefixed number, an `ART-NOTE-` id, and uses `content[]` instead of `sentences[]`:

```json
{
  "id": "ART-NOTE-A-4-1-1-3--1-",
  "number": "A-4.1.1.3.(1)",
  "title": "Structural Integrity",
  "sentences": [],
  "content": [ ContentItem ],
  "tables": [],
  "figures": [],
  "equations": [],
  "references": [],
  "note_refs": [],
  "page_span": [627]
}
```

> **Identification:** Detect a NoteArticle by `id.startsWith("ART-NOTE-")` or `number.startsWith("A-")`. Detect a NotesSection by `id.startsWith("SEC-NOTES-")`.

---

### 3.7 Subsection

```json
{
  "id": "SUBSEC-4-1-6",
  "number": "4.1.6",
  "title": "Wind Load",
  "articles": [ Article ],
  "page_span": [510, 511, ...]
}
```

| Field | Type |
|---|---|
| `id` | `string` — `"SUBSEC-{n}-{m}-{k}"` |
| `number` | `string` |
| `title` | `string` |
| `articles` | `Article[]` |
| `page_span` | `number[]` |

---

### 3.8 Article — The Core Content Node

An **Article** maps to a 4-part numbered provision (e.g. `4.1.1.3`). Its legal content is structured as an ordered list of **Sentences**, each of which may contain **Clauses** and **Subclauses**.

```json
{
  "id": "ART-4-1-6-5",
  "number": "4.1.6.5",
  "title": "Snow Load on Lower Roofs",
  "sentences": [ Sentence ],
  "content": [],
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
| `id` | `string` | `"ART-{n}-{m}-{k}-{j}"` or `"ART-AUTO-{n}"` for unnumbered |
| `number` | `string` | Dotted number e.g. `"4.1.6.5"` |
| `title` | `string` | Article heading |
| `sentences` | `Sentence[]` | Ordered numbered sentences (see §3.8.1) |
| `content` | `ContentItem[]` | Used **only** for note articles / unnumbered fallback — empty for regular code articles |
| `tables` | `Table[]` | Article-level tables (see §3.9) |
| `figures` | `Figure[]` | Figure metadata and image paths (see §3.10) |
| `equations` | `Equation[]` | Block equations with LaTeX (see §3.11) |
| `references` | `Reference[]` | Outgoing cross-references (see §3.12) |
| `note_refs` | `NoteRef[]` | Appendix note references (see §3.13) |
| `page_span` | `number[]` | Page numbers this article spans |

> For regular code articles, `content[]` is always `[]`. Use `sentences[]` to access the legal text.

---

### 3.8.1 Sentence

A **Sentence** maps to a numbered item within an Article — e.g. `1)`, `2)`, `3)`. Its full contextual number is `4.1.1.3.(2)`.

```json
{
  "id": "SENT-4-1-6-5-1",
  "number": "4.1.6.5.(1)",
  "marker": "1)",
  "content": "The snow load, S, on a roof or other surface...",
  "clauses": [ Clause ],
  "tables": [],
  "figures": [],
  "equations": [],
  "references": [],
  "page_span": [530]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"SENT-{art_safe}-{n}"` e.g. `"SENT-4-1-6-5-1"` |
| `number` | `string` | Full contextual number e.g. `"4.1.6.5.(1)"` |
| `marker` | `string` | Raw marker as it appeared: `"1)"`, `"2)"`, etc. |
| `content` | `string` | Introductory or full text of the sentence (before any clause list) |
| `clauses` | `Clause[]` | Lettered clause items under this sentence (see §3.8.2) |
| `tables` | `Table[]` | Tables attached to this sentence |
| `figures` | `Figure[]` | Figures attached to this sentence |
| `equations` | `Equation[]` | Equations attached to this sentence |
| `references` | `Reference[]` | Cross-references found in this sentence |
| `page_span` | `number[]` | |

> If `clauses[]` is empty, all legal text is in `content`. If `clauses[]` is populated, `content` holds the introductory preamble before the clause list.

---

### 3.8.2 Clause

A **Clause** maps to a lettered item under a Sentence — e.g. `(a)`, `(b)`, `(c)`. Its full contextual number is `4.1.1.3.(2)(a)`.

```json
{
  "id": "CLAUSE-4-1-6-5-1-a",
  "number": "4.1.6.5.(1)(a)",
  "marker": "(a)",
  "content": "the specified snow load, Ss, from...",
  "subclauses": [ Subclause ],
  "tables": [],
  "figures": [],
  "equations": [],
  "references": [],
  "page_span": [530]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"CLAUSE-{art_safe}-{sent_n}-{letter}"` e.g. `"CLAUSE-4-1-6-5-1-a"` |
| `number` | `string` | Full contextual number e.g. `"4.1.6.5.(1)(a)"` |
| `marker` | `string` | Raw marker: `"(a)"`, `"(b)"`, etc. |
| `content` | `string` | Text of this clause (intro text before any subclause list) |
| `subclauses` | `Subclause[]` | Roman-numeral subclause items (see §3.8.3) |
| `tables` | `Table[]` | Tables attached to this clause |
| `figures` | `Figure[]` | Figures attached to this clause |
| `equations` | `Equation[]` | Equations attached to this clause |
| `references` | `Reference[]` | Cross-references in this clause |
| `page_span` | `number[]` | |

> If `subclauses[]` is empty, all legal text is in `content`. If `subclauses[]` is populated, `content` holds the introductory preamble before the subclause list.

---

### 3.8.3 Subclause

A **Subclause** maps to a roman-numeral item under a Clause — e.g. `(i)`, `(ii)`, `(iii)`. Its full contextual number is `4.1.1.3.(2)(a)(i)`.

```json
{
  "id": "SUBCLAUSE-CLAUSE-4-1-6-5-1-a-i",
  "number": "4.1.6.5.(1)(a)(i)",
  "marker": "(i)",
  "content": "the specified snow load on the upper roof...",
  "page_span": [530],
  "references": []
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"SUBCLAUSE-{clause_id_safe}-{roman}"` |
| `number` | `string` | Full contextual number e.g. `"4.1.6.5.(1)(a)(i)"` |
| `marker` | `string` | Raw marker: `"(i)"`, `"(ii)"`, etc. |
| `content` | `string` | Full text of this subclause |
| `page_span` | `number[]` | |
| `references` | `Reference[]` | Cross-references in this subclause |

---

### 3.8.4 ContentItem — Fallback Inline Content (Notes / Legacy)

`ContentItem` objects appear only in `article.content[]` for **note articles** and unnumbered fallback articles. They do **not** appear in regular code articles (which use `sentences[]` instead).

```typescript
type ContentItemType = "text" | "equation" | "figure" | "table";

interface ContentItem {
  type:       ContentItemType;
  value:      string;   // text body, equation ID, table caption, or ""
  latex:      string;   // LaTeX string — only for type="equation"
  figure_id:  string;   // e.g. "FIG-56"  — only for type="figure"
  image_key:  string;   // filename hash — only for type="figure"
  image_path: string;   // relative path  — only for type="figure"
  caption:    string;   // figure caption  — only for type="figure"
  alt_text:   string;   // figure alt text — only for type="figure"
  table_id:   string;   // e.g. "TBL-218" — only for type="table"
  marker:     string;   // always "" in current output
}
```

> The `"sub_clause"` ContentItem type from previous schema versions no longer exists. Lettered items are now explicit `Clause` nodes under `sentence.clauses[]`.

---

### 3.9 Table

Tables now use a fully structured schema. `caption` is a parsed object, `headers` are indexed objects, and `rows` are structured with per-cell reference extraction.

```json
{
  "id": "TBL-2",
  "caption": {
    "raw": "Table 1.1.1.1.(5) Alternate Compliance Methods for Heritage Buildings Forming Part of Sentence 1.1.1.1.(5)",
    "table_number": "1.1.1.1.(5)",
    "table_label": "Table 1.1.1.1.(5)",
    "title": "Alternate Compliance Methods for Heritage Buildings",
    "forming_part_of": {
      "kind": "Sentence",
      "raw": "Sentence 1.1.1.1.(5)",
      "number": "1.1.1.1.(5)",
      "target_id": "SENT-1-1-1-1-5",
      "resolved": true
    }
  },
  "headers": [
    { "index": 0, "text": "No." },
    { "index": 1, "text": "Code Requirement in Division B" },
    { "index": 2, "text": "Alternate Compliance Method" }
  ],
  "rows": [
    {
      "row_id": "TBL-2-R1",
      "cells": [
        {
          "col_index": 0,
          "header": "No.",
          "raw": "1",
          "value": "1",
          "references": []
        },
        {
          "col_index": 1,
          "header": "Code Requirement in Division B",
          "raw": "Fire Separations Sentence 3.1.3.1.(1), Table 3.1.3.1., Subsection 9.10.9. ...",
          "value": "Fire Separations Sentence 3.1.3.1.(1), Table 3.1.3.1., Subsection 9.10.9. ...",
          "references": [
            {
              "text": "Sentence 3.1.3.1.(1)",
              "kind": "Sentence",
              "number": "3.1.3.1.(1)",
              "target_id": "SENT-3-1-3-1-1",
              "resolved": true
            },
            {
              "text": "Table 3.1.3.1.",
              "kind": "Table",
              "number": "3.1.3.1",
              "target_id": "TBL-52",
              "resolved": true
            },
            {
              "text": "Subsection 9.10.9.",
              "kind": "Subsection",
              "number": "9.10.9",
              "target_id": "SEC-9-10-9",
              "resolved": false
            }
          ]
        },
        {
          "col_index": 2,
          "header": "Alternate Compliance Method",
          "raw": "Except for F1 occupancies...",
          "value": "Except for F1 occupancies...",
          "references": []
        }
      ],
      "page_span": [32]
    }
  ],
  "references": [
    {
      "text": "Sentence 1.1.1.1.(5)",
      "kind": "Sentence",
      "number": "1.1.1.1.(5)",
      "target_id": "SENT-1-1-1-1-5",
      "resolved": true,
      "source": "caption"
    },
    {
      "text": "Sentence 3.1.3.1.(1)",
      "kind": "Sentence",
      "number": "3.1.3.1.(1)",
      "target_id": "SENT-3-1-3-1-1",
      "resolved": true,
      "source": "cell"
    }
  ],
  "page": 32,
  "page_span": [32]
}
```

#### 3.9.1 Table Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"TBL-{n}"` |
| `caption` | `TableCaption` | Structured caption object (see §3.9.2) |
| `headers` | `Header[]` | Structured column headers (see §3.9.3) |
| `rows` | `Row[]` | Structured data rows with cell-level references (see §3.9.4) |
| `references` | `TableReference[]` | Deduplicated references extracted from caption + all cells (see §3.9.5) |
| `page` | `number` | Page where the table starts |
| `page_span` | `number[]` | All pages this table covers (multi-page tables after merging) |
| `column_semantics` | `string[]` | AI-generated semantic labels per column (present only when `--ai` flag used) |

#### 3.9.2 TableCaption Object

| Field | Type | Description |
|---|---|---|
| `raw` | `string` | Original caption string exactly as in the PDF |
| `table_number` | `string` | Extracted table number e.g. `"1.1.1.1.(5)"` or `"4.1.6.5.-B"` |
| `table_label` | `string` | `"Table {table_number}"` — ready-to-display label |
| `title` | `string` | Descriptive title text (caption minus the table label and forming_part_of suffix) |
| `forming_part_of` | `FormingPartOf \| null` | Parsed "Forming Part of …" reference, or `null` if absent |

**FormingPartOf Object:**

| Field | Type | Description |
|---|---|---|
| `kind` | `string` | Reference type: `"Sentence"`, `"Article"`, `"Subsection"`, etc. |
| `raw` | `string` | Full raw reference text e.g. `"Sentence 1.1.1.1.(5)"` |
| `number` | `string` | Numeric identifier e.g. `"1.1.1.1.(5)"` |
| `target_id` | `string` | Resolved document node ID e.g. `"SENT-1-1-1-1-5"` (empty string if unresolved) |
| `resolved` | `boolean` | `true` if the target exists in this document |

#### 3.9.3 Header Object

| Field | Type | Description |
|---|---|---|
| `index` | `number` | Zero-based column index |
| `text` | `string` | Header label text |

#### 3.9.4 Row and Cell Objects

Each row in `rows[]` is a `Row` object:

| Field | Type | Description |
|---|---|---|
| `row_id` | `string` | `"TBL-{n}-R{rowIndex}"` e.g. `"TBL-2-R1"` |
| `cells` | `Cell[]` | Ordered array of cell objects, one per column |
| `page_span` | `number[]` | Pages this row appears on (inherits from table `page_span`) |

Each `Cell` object:

| Field | Type | Description |
|---|---|---|
| `col_index` | `number` | Zero-based column index |
| `header` | `string` | Text of the column header for this cell |
| `raw` | `string` | Raw cell text as extracted from the PDF |
| `value` | `string` | Same as `raw` (available for future normalization) |
| `references` | `CellReference[]` | Structured references extracted from this cell's text |

Each `CellReference` object:

| Field | Type | Description |
|---|---|---|
| `text` | `string` | Original reference text as found in the cell e.g. `"Sentence 3.1.3.1.(1)"` |
| `kind` | `string` | One of: `"Sentence"`, `"Article"`, `"Subsection"`, `"Section"`, `"Clause"`, `"Table"`, `"Figure"`, `"Appendix"` |
| `number` | `string` | Extracted numeric identifier e.g. `"3.1.3.1.(1)"` |
| `target_id` | `string` | Resolved document node ID (empty string `""` if unresolved) |
| `resolved` | `boolean` | `true` if the target exists in this document |

#### 3.9.5 Table-Level References

`table.references[]` is a deduplicated union of all references found anywhere in the table — from the caption's `forming_part_of` and from every cell. Each entry has all the `CellReference` fields plus:

| Additional Field | Type | Description |
|---|---|---|
| `source` | `string` | `"caption"` if extracted from the caption, `"cell"` if from a row cell |

> **Resolution stats:** 724 total table references extracted across 388 tables; 679 resolved (93.8%). Unresolved references point to external BCBC volumes not in this PDF.

> **Cells may contain LaTeX math** (backslash notation). Render with KaTeX or MathJax.

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
| `target_id` | `string` | ID of the referenced node (e.g. `"ART-4-1-6-5"`, `"TBL-217"`, `"FIG-3"`) |
| `resolved` | `boolean` | `true` if target exists in this document; `false` if it points to an external volume |

> Unresolved references (~15%) point to other BCBC volumes not in this PDF. Only render links when `resolved: true`.

---

### 3.13 NoteRef

```json
{
  "raw": "See Note A-1.1.1.1.(3).",
  "note_ref": "A-1.1.1.1.(3).",
  "target_ids": ["ART-NOTE-A-1-1-1-1--3-"],
  "resolved": true
}
```

| Field | Type | Description |
|---|---|---|
| `raw` | `string` | Full original text including "See Note " |
| `note_ref` | `string` | The extracted note identifier |
| `target_ids` | `string[]` | Array of article IDs (can resolve to multiple) |
| `resolved` | `boolean` | `true` if all targets exist in this document |

> `target_ids` now contains `ART-NOTE-*` IDs (previously `CL-NOTE-*`). Update any frontend lookups accordingly.

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

> Appendix sections use the same Article/Sentence/Clause/Subclause hierarchy as regular Part sections.

---

## 4. ID Naming Conventions

| Entity | Pattern | Example |
|---|---|---|
| Division | `DIV-{letter}` | `DIV-B` |
| Part | `PART-{div}-{n}` | `PART-B-4` |
| Section | `SEC-{n}-{m}` | `SEC-4-1` |
| Notes Section | `SEC-NOTES-{part_id}` | `SEC-NOTES-PART-B-4` |
| Subsection | `SUBSEC-{n}-{m}-{k}` | `SUBSEC-4-1-6` |
| Article (numbered) | `ART-{n}-{m}-{k}-{j}` | `ART-4-1-6-5` |
| Article (unnumbered) | `ART-AUTO-{n}` | `ART-AUTO-153` |
| Note Article | `ART-NOTE-{A-num}` | `ART-NOTE-A-4-1-1-3--1-` |
| Sentence | `SENT-{art_safe}-{n}` | `SENT-4-1-6-5-1` |
| Clause (lettered) | `CLAUSE-{art_safe}-{sent_n}-{letter}` | `CLAUSE-4-1-6-5-1-a` |
| Subclause (roman) | `SUBCLAUSE-{clause_id_safe}-{roman}` | `SUBCLAUSE-CLAUSE-4-1-6-5-1-a-i` |
| Table | `TBL-{n}` | `TBL-218` |
| Figure | `FIG-{n}` | `FIG-56` |
| Equation | `EQ-{n}` | `EQ-13` |
| Appendix | `APP-{div}-{letter}` | `APP-B-C` |
| Preface section | `PREF-SEC-{nn}` | `PREF-SEC-01` |

> Dots in article numbers are replaced with hyphens: `4.1.6.5` → `ART-4-1-6-5`.
> For note articles, `.` `(` `)` are all replaced with `-`: `A-4.1.1.3.(1)` → `ART-NOTE-A-4-1-1-3--1-`.

---

## 5. Document Tree — Full Hierarchy Diagram

```
Document
├── title, source_pdf, total_pages, _stats
│
├── preface
│   └── sections[]
│       ├── id, number, title, page_span
│       ├── content[]  ← ContentItem[]
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
│   │       │   │   └── articles[]   ←── PRIMARY CONTENT LOCATION
│   │       │   │       ├── id="ART-4-1-6-5", number="4.1.6.5", title
│   │       │   │       ├── sentences[]   ← Sentence[]
│   │       │   │       │   ├── id="SENT-4-1-6-5-1", number="4.1.6.5.(1)"
│   │       │   │       │   ├── marker="1)", content="intro text..."
│   │       │   │       │   ├── clauses[]   ← Clause[]
│   │       │   │       │   │   ├── id="CLAUSE-4-1-6-5-1-a", marker="(a)"
│   │       │   │       │   │   ├── content="clause text..."
│   │       │   │       │   │   └── subclauses[]   ← Subclause[]
│   │       │   │       │   │       ├── id="SUBCLAUSE-...-i", marker="(i)"
│   │       │   │       │   │       └── content="subclause text..."
│   │       │   │       │   ├── tables[], figures[], equations[], references[]
│   │       │   │       │   └── page_span
│   │       │   │       ├── content[]       ← always [] for regular articles
│   │       │   │       ├── tables[]        ← article-level Table[]
│   │       │   │       ├── figures[]       ← Figure[]
│   │       │   │       ├── equations[]     ← Equation[]
│   │       │   │       ├── references[]    ← Reference[]
│   │       │   │       └── note_refs[]     ← NoteRef[]
│   │       │   └── articles[]   ←── (direct section articles, less common)
│   │       └── [Notes Section]  id="SEC-NOTES-PART-B-4", number=""
│   │           ├── id, number="", title, page_span
│   │           ├── subsections[]  ← always []
│   │           └── articles[]   ←── NOTE ARTICLES (direct, no subsection nesting)
│   │               ├── id="ART-NOTE-A-4-1-1-3--1-", number="A-4.1.1.3.(1)"
│   │               ├── title, page_span
│   │               ├── sentences[]  ← always [] for note articles
│   │               ├── content[]    ← ContentItem[] (note text here)
│   │               ├── tables[], figures[], equations[]
│   │               ├── references[]    ← Reference[]
│   │               └── note_refs[]     ← NoteRef[]
│   └── appendices[]
│       ├── id, number, title, page_span
│       └── sections[]  (same Article/Sentence/Clause structure as Regular Section above)
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
| `GET` | `/document` | Full document tree (large — ~19.9 MB) |
| `GET` | `/document/summary` | Lightweight nav tree (parts + section article counts only) |
| `GET` | `/section/{section_id}` | Single section with its articles |
| `GET` | `/clause/{clause_id}` | Single article + `_breadcrumb` context (accepts `ART-*` IDs) |
| `GET` | `/search?q={term}` | Full-text search (max 50 results) |
| `GET` | `/references/{node_id}` | Reverse lookup: which articles reference this node |

---

## 7. Frontend Rendering Guidance

### Legal Text Rendering

The legal text is now structured as a proper hierarchy — do **not** attempt to render it as a flat list:

```
Article heading
  └── 1) Sentence intro text...
        └── (a) Clause text...
              └── (i) Subclause text...
              └── (ii) Subclause text...
        └── (b) Clause text...
  └── 2) Sentence text (no clauses)
```

**Rendering order within an Article:**
1. Render `article.title` as the article heading.
2. For each `sentence` in `article.sentences[]` (in array order):
   - Render `sentence.marker` + `sentence.content` as the sentence opening.
   - For each `clause` in `sentence.clauses[]`: render `clause.marker` + `clause.content`.
     - For each `subclause` in `clause.subclauses[]`: render `subclause.marker` + `subclause.content`.
   - If `sentence.clauses[]` is empty, `sentence.content` is the complete text.
3. Render `article.tables[]`, `article.figures[]`, `article.equations[]` at article level.

### Math

- **Inline math** in `content` strings on Sentence/Clause/Subclause: delimited by `$...$` → render with KaTeX inline mode.
- **Block equations** in `Equation` objects: use the `latex` field → render with KaTeX `\displaystyle` or MathJax block mode.
- **Table cells** may also contain LaTeX notation (e.g. Greek letters like `\beta`).

### Images

- Figures are served from `storage/figures/{image_key}`.
- Always use `image_key` to build URLs; `image_path` uses Windows backslashes and is not suitable as-is.
- Always render `alt_text` for accessibility.

### Tables

With the new structured table schema:

1. Read `table.caption.raw` for the full caption string, or `table.caption.title` for a clean display title.
2. If `table.caption.forming_part_of` is non-null and `resolved: true`, render it as a link using `target_id`.
3. Build table header row from `table.headers[]` — each is `{ index, text }`.
4. Build data rows from `table.rows[]`. Each row has a `row_id` and `cells[]`. Access cell text via `cell.value`. Render `cell.references[]` as inline hyperlinks within the cell — only when `resolved: true`.
5. Use `table.references[]` to render a "Referenced Provisions" summary panel beneath the table — filter by `source: "caption"` or `source: "cell"` as needed.

```typescript
function renderTable(table: Table) {
  const title = table.caption.title || table.caption.raw;
  const headers = table.headers.map(h => h.text);
  const rows = table.rows.map(row =>
    row.cells.map(cell => ({
      text: cell.value,
      links: cell.references.filter(r => r.resolved),
    }))
  );
  // render headers, rows, and optional forming_part_of link
}
```

### References / Links

- Only render `references[]` entries as clickable links when `resolved: true`.
- `target_id` maps directly to the ID system above — use it to build deep links (e.g. `ART-4-1-6-5`, `TBL-217`, `FIG-3`).
- For `note_refs[]`, `target_ids` is an array — a note may link to multiple articles. IDs are `ART-NOTE-*`.
- For table cell references (`cell.references[]`), the same `resolved` / `target_id` pattern applies — render inline hyperlinks only when `resolved: true`.

### Traversal Pattern

```
Document → divisions[] → parts[] → sections[] → subsections[] → articles[]
                                               ↘ articles[]  (also check here)
```

When traversing `part.sections[]`, a section is a **NotesSection** when `section.id.startsWith("SEC-NOTES-")`. Notes sections hold articles directly in `section.articles[]` — skip the subsections loop.

```typescript
for (const section of part.sections) {
  if (section.id.startsWith("SEC-NOTES-")) {
    // Notes section — articles are direct children, use content[] not sentences[]
    renderNoteArticles(section.articles);
  } else {
    // Regular section — articles are inside subsections
    for (const sub of section.subsections) {
      renderArticles(sub.articles);
    }
    // Also check direct section articles (uncommon)
    if (section.articles.length) renderArticles(section.articles);
  }
}
```

### Article vs Note Article

```typescript
function isNoteArticle(article: Article): boolean {
  return article.id.startsWith("ART-NOTE-") || article.number.startsWith("A-");
}

function renderArticle(article: Article) {
  if (isNoteArticle(article)) {
    // Note article: render article.content[] as flat ContentItems
    renderContentItems(article.content);
  } else {
    // Regular code article: render article.sentences[]
    for (const sentence of article.sentences) {
      renderSentence(sentence);
    }
  }
}
```

### Notes Articles

- A note article has `id` starting with `"ART-NOTE-"` and `number` starting with `"A-"`.
- Its `content[]` follows the ContentItem schema (§3.8.4). `sentences[]` is always empty.
- Render notes sections with a distinct visual style (e.g., collapsible panel, different background) to distinguish them from normative code content.
- The `note_refs[]` on regular sentences/articles (e.g. `"See Note A-4.1.1.3.(1)."`) resolve to `target_ids` containing `ART-NOTE-*` IDs — use these to deep-link into the notes section.

### Navigation Data

- Use `GET /document/summary` to build a navigation tree without loading all article content.
- `page_span` on every node allows mapping to original PDF page numbers for a "view in PDF" link.
- Notes sections appear at the end of their Part's `sections[]` array.

---

## 8. Migration Guide (from Previous Schema)

If your frontend was built against the previous schema (`clauses[]` / `CL-*` IDs), here is what changed:

### 8.1 Article / Clause Hierarchy

| Previous | Now |
|---|---|
| `subsection.clauses[]` | `subsection.articles[]` |
| `section.clauses[]` | `section.articles[]` |
| Clause id: `CL-4-1-6-5` | Article id: `ART-4-1-6-5` |
| Note clause id: `CL-NOTE-A-...` | Note article id: `ART-NOTE-A-...` |
| `clause.content[]` (mixed ContentItems) | `article.sentences[]` with nested Clause/Subclause nodes |
| `ContentItem { type: "sub_clause", marker: "(a)" }` | Explicit `Clause` node in `sentence.clauses[]` |
| No Sentence node | `Sentence` node in `article.sentences[]` |
| No Subclause node | `Subclause` node in `clause.subclauses[]` |
| `note_refs[].target_ids` → `CL-NOTE-*` | `note_refs[].target_ids` → `ART-NOTE-*` |

### 8.2 Table Schema (New — this version)

The table schema has been enriched from flat strings to fully structured objects:

| Field | Previous type | New type | Notes |
|---|---|---|---|
| `caption` | `string` | `TableCaption` object | Use `caption.raw` for the plain string; `caption.title` for display; `caption.forming_part_of` for the contextual reference |
| `headers` | `string[]` | `Header[]` (`{index, text}`) | Use `header.text` to get the column label |
| `rows` | `string[][]` | `Row[]` (`{row_id, cells[], page_span}`) | Access cell text via `row.cells[n].value`; links via `row.cells[n].references[]` |
| `page` | `number` | `number` (unchanged) | Still present |
| `page_span` | *(absent)* | `number[]` | Pages covered (useful for merged multi-page tables) |
| `references` | *(absent)* | `TableReference[]` | Deduplicated union of all refs from caption + cells, each with a `source` field |

**Quick adapter for existing code** — if you currently access tables like `table.caption` (string) and `table.rows[i][j]` (string), update to:

```typescript
// Before:
const captionText = table.caption;
const cellText = table.rows[i][j];

// After:
const captionText = table.caption.raw;
const cellText = table.rows[i].cells[j].value;
const cellRefs = table.rows[i].cells[j].references;  // new: structured links
const headerLabel = table.headers[j].text;            // new: indexed headers
```
