# Frontend Schema Briefing — BCBC 2024 Structured Document

**Source file:** `storage/output/structured_document.json` (~43.6 MB)
**Document:** British Columbia Building Code 2024 (1906 pages)
**Last updated:** 2026-04-11 (post-fix regeneration — subsection IDs, table captions, figure schema)

---

## 1. Overview

The JSON document is a fully parsed, hierarchically structured representation of the BCBC 2024 PDF. It organizes the code into the full legal hierarchy:

**Divisions → Parts → Sections → Subsections → Articles → Sentences → Clauses → Subclauses**

Each **Article** (a 4-part numbered provision like `4.1.1.3`) contains explicit **Sentence** nodes for numbered items (`1)`, `2)`), which in turn hold **Clause** nodes for lettered items (`(a)`, `(b)`), which hold **Subclause** nodes for roman-numeral items (`(i)`, `(ii)`). This replaces any previous flat `content[]` approach.

Cross-references and appendix note references are resolved and embedded per-article. Each Part that contains a "Notes to Part" section in the PDF also includes a dedicated **Notes Section** (`SEC-NOTES-*`) at the same level as regular code sections. Notes sections hold note articles (`ART-NOTE-*`) directly — no subsection nesting.

### Scale (actual counts from regenerated file)

| Entity | Count |
|---|---|
| Divisions | 3 |
| Parts | 15 |
| Sections | 114 |
| Subsections | 445 |
| Articles | 3,118 |
| Sentences | 5,663 |
| Clauses (lettered) | 3,695 |
| Subclauses (roman) | 111 |
| Tables | 469 |
| Figures | 212 |
| Equations | 110 |
| Cross-references | 2,945 (97.4% resolved) |
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
  "resolved_references": 2867,
  "resolution_rate_pct": 97.4,
  "total_note_refs": 922,
  "resolved_note_refs": 920,
  "note_resolution_rate_pct": 99.8
}
```

| Field | Type | Description |
|---|---|---|
| `total_references` | `number` | Total cross-references found across all clauses and table cells |
| `resolved_references` | `number` | References that successfully map to a node in this document |
| `resolution_rate_pct` | `number` | `resolved / total * 100` |
| `total_note_refs` | `number` | Total "See Note A-…" appendix note references |
| `resolved_note_refs` | `number` | Note refs that resolved to an article in this document |
| `note_resolution_rate_pct` | `number` | Note resolution percentage |

> **97.4% overall resolution** (up from 84.7% in prior version). Remaining ~2.6% point to other BCBC volumes not in this PDF.

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

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Always `"PREFACE"` |
| `title` | `string` | Always `"Preface"` |
| `sections` | `PrefaceSection[]` | Ordered preface sections |
| `page_span` | `number[]` | Pages covered |

**PrefaceSection** — uses `content[]` directly (no articles/sentences):

```json
{
  "id": "PREF-SEC-01",
  "number": "",
  "title": "Preface Content",
  "content": [ ContentItem ],
  "subsections": [ PrefaceSubsection ],
  "page_span": [11]
}
```

**PrefaceSubsection:**

```json
{
  "id": "PREF-SUBSEC-01-02",
  "number": "",
  "title": "Division A — Compliance",
  "content": [ ContentItem ],
  "tables": [],
  "figures": [],
  "references": [],
  "page_span": [11]
}
```

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

**ConversionSection** — contains `content[]` and `tables[]` directly (no articles):

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
| `parts` | `Part[]` | Parts within this division |
| `appendices` | `Appendix[]` | Appendices (only DIV-B has appendices in BCBC 2024) |
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
| `id` | `string` | `"SEC-{n}-{m}"` for numeric sections |
| `number` | `string` | e.g. `"4.1"` |
| `title` | `string` | |
| `subsections` | `Subsection[]` | Usually populated; `articles[]` may be empty |
| `articles` | `Article[]` | Direct articles (uncommon — most are inside subsections) |
| `page_span` | `number[]` | |

> **Traversal note:** Most articles live under **Subsections**, not Sections directly. Always check both `section.subsections[].articles[]` and `section.articles[]` when traversing.

---

### 3.6a Notes Section — Part Notes (Special Section Type)

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

**Parts with Notes Sections:**

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

**NoteArticle** — same outer shape as a regular Article (§3.8) but with an `A-`-prefixed number and `ART-NOTE-` id. Uses `content[]` instead of `sentences[]`:

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

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"SUBSEC-{n}-{m}-{k}"` — always `SUBSEC-` prefix |
| `number` | `string` | 3-part number e.g. `"4.1.6"` |
| `title` | `string` | Subsection heading |
| `articles` | `Article[]` | Articles within this subsection |
| `page_span` | `number[]` | |

> **Subsection vs Section IDs:** Subsections use the `SUBSEC-` prefix. Cross-references to subsections (kind=`"Subsection"`) resolve to `SUBSEC-*` target IDs, never `SEC-*`. This distinction is critical for hyperlink resolution.

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
| `content` | `ContentItem[]` | Used **only** for note articles / unnumbered fallback — always `[]` for regular code articles |
| `tables` | `Table[]` | Article-level tables (see §3.9) |
| `figures` | `Figure[]` | Figure metadata and image paths (see §3.10) |
| `equations` | `Equation[]` | Block equations with LaTeX (see §3.11) |
| `references` | `Reference[]` | Outgoing cross-references extracted from text (see §3.12) |
| `note_refs` | `NoteRef[]` | Appendix note references extracted from text (see §3.13) |
| `page_span` | `number[]` | Page numbers this article spans |

> For regular code articles, `content[]` is always `[]`. Use `sentences[]` to access the legal text.

---

### 3.8.1 Sentence

A **Sentence** maps to a numbered item within an Article — e.g. `1)`, `2)`, `3)`. Its full contextual number is `4.1.6.5.(1)`.

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
| `content` | `string` | Introductory or complete text of the sentence (before any clause list) |
| `clauses` | `Clause[]` | Lettered clause items under this sentence (see §3.8.2) |
| `tables` | `Table[]` | Tables attached to this sentence |
| `figures` | `Figure[]` | Figures attached to this sentence |
| `equations` | `Equation[]` | Equations attached to this sentence |
| `references` | `Reference[]` | Cross-references found in this sentence's text |
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
| `references` | `Reference[]` | Cross-references in this clause's text |
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
| `references` | `Reference[]` | Cross-references in this subclause's text |

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
  caption:    string;   // figure caption raw string — only for type="figure"
  alt_text:   string;   // figure alt text — only for type="figure"
  table_id:   string;   // e.g. "TBL-218" — only for type="table"
  marker:     string;   // always "" in current output
}
```

> The `"sub_clause"` ContentItem type from previous schema versions no longer exists. Lettered items are now explicit `Clause` nodes under `sentence.clauses[]`.

---

### 3.9 Table

Tables use a fully structured schema. `caption` is a parsed object, `headers` are indexed objects, and `rows` are structured with per-cell reference extraction.

```json
{
  "id": "TBL-12",
  "caption": {
    "raw": "Table 1.3.1.2. Documents Referenced in Book I (General) of the British Columbia Building Code (1) (2) Forming Part of Sentence 1.3.1.2.(1)",
    "table_number": "1.3.1.2.",
    "table_label": "Table 1.3.1.2.",
    "title": "Documents Referenced in Book I (General) of the British Columbia Building Code (1) (2)",
    "forming_part_of": {
      "kind": "Sentence",
      "raw": "Sentence 1.3.1.2.(1)",
      "number": "1.3.1.2.(1)",
      "target_id": "SENT-1-3-1-2-1",
      "resolved": true
    }
  },
  "headers": [
    { "index": 0, "text": "Issuing Agency" },
    { "index": 1, "text": "Document Number" },
    { "index": 2, "text": "Title of Document" },
    { "index": 3, "text": "Code Reference" }
  ],
  "rows": [
    {
      "row_id": "TBL-12-R1",
      "cells": [
        {
          "col_index": 0,
          "header": "Issuing Agency",
          "raw": "AAMA",
          "value": "AAMA",
          "references": []
        },
        {
          "col_index": 1,
          "header": "Document Number",
          "raw": "501-05",
          "value": "501-05",
          "references": []
        },
        {
          "col_index": 2,
          "header": "Title of Document",
          "raw": "Methods of Test for Exterior Walls",
          "value": "Methods of Test for Exterior Walls",
          "references": []
        },
        {
          "col_index": 3,
          "header": "Code Reference",
          "raw": "A-5.9.3.",
          "value": "A-5.9.3.",
          "references": []
        }
      ],
      "page_span": [97]
    }
  ],
  "references": [
    {
      "text": "Sentence 1.3.1.2.(1)",
      "kind": "Sentence",
      "number": "1.3.1.2.(1)",
      "target_id": "SENT-1-3-1-2-1",
      "resolved": true,
      "source": "caption"
    }
  ],
  "page": 97,
  "page_span": [97]
}
```

#### 3.9.1 Table Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"TBL-{n}"` — sequential counter across the full document |
| `caption` | `TableCaption` | Structured caption object (see §3.9.2) |
| `headers` | `Header[]` | Structured column headers (see §3.9.3) |
| `rows` | `Row[]` | Structured data rows with per-cell reference extraction (see §3.9.4) |
| `references` | `TableReference[]` | Deduplicated references from caption + all cells (see §3.9.5) |
| `page` | `number` | Page where the table starts |
| `page_span` | `number[]` | All pages this table covers (multi-page tables are merged) |
| `column_semantics` | `string[]` | AI-generated semantic labels per column — present only when `--ai` flag used at pipeline time |

#### 3.9.2 TableCaption Object

The caption is always a structured object, never a plain string.

| Field | Type | Description |
|---|---|---|
| `raw` | `string` | Original full caption string exactly as extracted from the PDF |
| `table_number` | `string` | Extracted table identifier including trailing dot when present in source (e.g. `"1.3.1.2."`, `"4.1.5.3."`, `"1.1.1.1.(5)"`) |
| `table_label` | `string` | `"Table {table_number}"` — ready-to-display label e.g. `"Table 1.3.1.2."` |
| `title` | `string` | Descriptive title text: caption minus the table label and "Forming Part of" suffix. Never starts with `"."` |
| `forming_part_of` | `FormingPartOf \| null` | Parsed "Forming Part of …" reference, or `null` if absent |

> **Trailing dot rule:** When the PDF source has a trailing period after the table number (e.g. `"Table 4.1.5.3. Specified..."`) both `table_number` and `table_label` preserve that dot. Do not strip it when displaying — it is part of the canonical table identifier in BCBC.

**FormingPartOf Object:**

| Field | Type | Description |
|---|---|---|
| `kind` | `string` | Reference type: `"Sentence"`, `"Article"`, `"Subsection"`, `"Section"`, etc. |
| `raw` | `string` | Full raw reference text e.g. `"Sentence 4.1.5.3.(1)"` |
| `number` | `string` | Extracted numeric identifier e.g. `"4.1.5.3.(1)"` |
| `target_id` | `string` | Resolved document node ID (empty string if unresolved) |
| `resolved` | `boolean` | `true` if the target exists in this document |

#### 3.9.3 Header Object

| Field | Type | Description |
|---|---|---|
| `index` | `number` | Zero-based column index |
| `text` | `string` | Header label text. Multi-row headers are collapsed with ` / ` separator |

> Multi-row `<thead>` with rowspan/colspan are fully resolved. The collapsed header label for a column with two header rows reads as `"Top Label / Sub Label"`.

#### 3.9.4 Row and Cell Objects

Each row in `rows[]` is a `Row` object:

| Field | Type | Description |
|---|---|---|
| `row_id` | `string` | `"TBL-{n}-R{rowIndex}"` e.g. `"TBL-12-R1"` (1-based row index) |
| `cells` | `Cell[]` | Ordered array of cell objects, one per column |
| `page_span` | `number[]` | Pages this row appears on (inherits table `page_span`) |

Each `Cell` object:

| Field | Type | Description |
|---|---|---|
| `col_index` | `number` | Zero-based column index |
| `header` | `string` | Text of the column header for this cell |
| `raw` | `string` | Raw cell text as extracted from the PDF |
| `value` | `string` | Same as `raw` (reserved for future normalization) |
| `references` | `CellReference[]` | Structured references extracted from this cell's text |

Each `CellReference` object (from cell text):

| Field | Type | Description |
|---|---|---|
| `text` | `string` | Full reference text as found in the cell e.g. `"Sentence 3.1.3.1.(1)"` |
| `kind` | `string` | One of: `"Sentence"`, `"Article"`, `"Subsection"`, `"Section"`, `"Clause"`, `"Table"`, `"Figure"`, `"Appendix"` |
| `number` | `string` | Extracted numeric identifier e.g. `"3.1.3.1.(1)"` |
| `target_id` | `string` | Resolved document node ID (empty string `""` if unresolved) |
| `resolved` | `boolean` | `true` if the target exists in this document |

> **Subsection cell references** now correctly resolve to `SUBSEC-*` target IDs (e.g. `"SUBSEC-9-10-9"`), not `"SEC-*"`. Use `target_id` directly for navigation.

#### 3.9.5 Table-Level References

`table.references[]` is a deduplicated union of all references found anywhere in the table — from the caption's `forming_part_of` and from every cell. Each entry has all the `CellReference` fields plus:

| Additional Field | Type | Description |
|---|---|---|
| `source` | `string` | `"caption"` if extracted from the caption's forming_part_of; `"cell"` if from a row cell |

> Only render references as hyperlinks when `resolved: true`. Unresolved references point to external BCBC volumes not in this PDF.

> **Cells may contain inline LaTeX math** (backslash notation). Render with KaTeX or MathJax.

---

### 3.10 Figure

Figures now use a fully structured schema. The `caption` field is a parsed object (never a plain string), and each figure has an explicit `reference_key` for canonical hyperlink matching.

```json
{
  "id": "FIG-55",
  "caption": {
    "raw": "Figure 4.1.6.5.-A",
    "figure_label": "Figure 4.1.6.5.-A",
    "figure_number": "4.1.6.5.-A",
    "title": ""
  },
  "alt_text": "Diagram showing snow accumulation on a lower roof adjacent to a higher roof...",
  "image_key": "223b363465c3987e97bf7cf0bc1dbe0d_img.jpg",
  "image_path": "storage\\figures\\223b363465c3987e97bf7cf0bc1dbe0d_img.jpg",
  "page": 530,
  "reference_key": "Figure 4.1.6.5.-A",
  "page_span": [530]
}
```

Another example with a title:

```json
{
  "id": "FIG-4",
  "caption": {
    "raw": "Figure A-1.3.3.4.(2) Application of the definition of grade",
    "figure_label": "Figure A-1.3.3.4.(2)",
    "figure_number": "A-1.3.3.4.(2)",
    "title": "Application of the definition of grade"
  },
  "alt_text": "...",
  "image_key": "...",
  "image_path": "storage\\figures\\...",
  "page": 62,
  "reference_key": "Figure A-1.3.3.4.(2)",
  "page_span": [62]
}
```

#### 3.10.1 Figure Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"FIG-{n}"` — sequential counter across the full document |
| `caption` | `FigureCaption` | Structured caption object (see §3.10.2) |
| `alt_text` | `string` | Accessibility description text extracted from the PDF |
| `image_key` | `string` | Filename (MD5 hash-based) in `storage/figures/` e.g. `"223b363465c3987e97bf7cf0bc1dbe0d_img.jpg"` |
| `image_path` | `string` | Relative path from project root using Windows backslashes |
| `page` | `number` | Source page number |
| `reference_key` | `string` | Canonical string used for hyperlink resolution — equals `caption.figure_label` when parseable, or the raw caption otherwise |
| `page_span` | `number[]` | Page(s) this figure appears on |

> **`image_path` uses Windows backslashes.** Always use `image_key` to build URLs via the API: `GET /figures/{image_key}` or construct as `storage/figures/{image_key}`. Do not use `image_path` as-is on non-Windows systems.

#### 3.10.2 FigureCaption Object

The caption is always a structured object, never a plain string.

| Field | Type | Description |
|---|---|---|
| `raw` | `string` | Original full caption string exactly as extracted from the PDF |
| `figure_label` | `string` | `"Figure {figure_number}"` — canonical label e.g. `"Figure 4.1.6.5.-A"` |
| `figure_number` | `string` | The figure's identifier only, without the "Figure" prefix e.g. `"4.1.6.5.-A"` or `"A-1.3.3.4.(2)"` |
| `title` | `string` | Descriptive title text (caption minus the figure label). Empty string `""` when no title present |

**Figure number formats encountered in BCBC 2024:**

| Pattern | Example | Meaning |
|---|---|---|
| `{n}.{m}.{k}.{j}-{L}` | `4.1.6.5.-A` | Numbered figure with letter suffix |
| `{n}.{m}.{k}.{j}-{L}` | `4.1.7.6.-C` | Multiple figure variants |
| `A-{n}.{m}.{k}.{j}` | `A-1.1.1.1.(6)` | Appendix figure |
| `A-{n}.{m}.{k}.{j}({s})-{L}` | `A-1.4.1.2.(1)-A` | Appendix figure with sentence and variant |
| `Table A-{n}.{m}.{k}.{j}-{L}` | `Table A-9.23.13.5.-A` | "Figure Table" hybrid (notes section) |

> **Empty captions:** 9 figures have `caption.raw = ""` and `reference_key = ""`. These are decorative or uncaptioned images that cannot be hyperlinked by caption. Detect with `figure.reference_key === ""`.

#### 3.10.3 Figure Reference Matching

When a text reference like `"Figure 4.1.6.5.-A"` is encountered:

1. **Exact match:** Look up `_cap_Figure 4.1.6.5.-A` in the reference index → direct hit via `reference_key`.
2. **Fuzzy match:** Normalize both sides (strip dots/hyphens/case) and compare `figure_number` values.
3. **Type guard:** Figure references only resolve to `FIG-*` nodes. Table references only resolve to `TBL-*` nodes. There is no cross-type collision even when figure and table numbers share the same digits.

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
| `id` | `string` | `"EQ-{n}"` — sequential counter |
| `latex` | `string` | LaTeX math string (without `$` delimiters) |
| `page` | `number` | Source page number |

> Render with `\[ ... \]` block display (MathJax) or KaTeX `\displaystyle` mode. Inline math within `content` strings on Sentence/Clause/Subclause is delimited by `$...$`.

---

### 3.12 Reference — Cross-Reference Objects

References appear in two locations with slightly different schemas:
- `article.references[]` / `sentence.references[]` / `clause.references[]` / `subclause.references[]` — extracted from prose text
- `table.references[]` and `cell.references[]` — extracted from table captions and cell text (covered in §3.9)

**Clause/Article-level reference (from prose text):**

```json
{
  "text": "Figure 4.1.6.5.-A",
  "kind": "Figure",
  "number": "4.1.6.5.-A",
  "target_id": "FIG-55",
  "resolved": true,
  "lookup_key": "Figure 4.1.6.5.-A"
}
```

```json
{
  "text": "Subsection 9.10.9.",
  "kind": "Subsection",
  "number": "9.10.9",
  "target_id": "SUBSEC-9-10-9",
  "resolved": true
}
```

```json
{
  "text": "Table 4.1.5.3.",
  "kind": "Table",
  "number": "4.1.5.3.",
  "target_id": "TBL-208",
  "resolved": true
}
```

| Field | Type | Description |
|---|---|---|
| `text` | `string` | Original reference text as it appeared in the PDF |
| `kind` | `string` | One of: `"Sentence"`, `"Article"`, `"Subsection"`, `"Section"`, `"Clause"`, `"Table"`, `"Figure"` |
| `number` | `string` | Extracted numeric/alphanumeric identifier |
| `target_id` | `string` | ID of the referenced node — e.g. `"ART-4-1-6-5"`, `"SUBSEC-9-10-9"`, `"TBL-208"`, `"FIG-55"` |
| `resolved` | `boolean` | `true` if target exists in this document; `false` if it points to an external volume |
| `lookup_key` | `string` | **Figure references only** — canonical matching key e.g. `"Figure 4.1.6.5.-A"`. Used to match against `figure.reference_key`. Absent on non-figure references |

**Target ID mapping by reference kind:**

| `kind` | Target ID prefix | Example |
|---|---|---|
| `Sentence` | `SENT-` | `SENT-4-1-6-5-1` |
| `Article` | `ART-` | `ART-4-1-6-5` |
| `Subsection` | `SUBSEC-` | `SUBSEC-9-10-9` |
| `Section` | `SEC-` | `SEC-4-1` |
| `Clause` | `ART-` | `ART-4-1-6-5` |
| `Table` | `TBL-` | `TBL-208` |
| `Figure` | `FIG-` | `FIG-55` |

> **Only render as clickable links when `resolved: true`.** Unresolved references (~2.6%) point to other BCBC volumes not in this PDF.

> **Subsection target IDs** always use `SUBSEC-*` prefix. Never `SEC-*`. If your frontend has existing logic mapping `Subsection` kind to `SEC-*`, update it to `SUBSEC-*`.

---

### 3.13 NoteRef — Appendix Note Reference

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
| `raw` | `string` | Full original text including "See Note " prefix |
| `note_ref` | `string` | The extracted note identifier e.g. `"A-1.1.1.1.(3)."` |
| `target_ids` | `string[]` | Array of `ART-NOTE-*` article IDs — can resolve to multiple articles |
| `resolved` | `boolean` | `true` if all targets exist in this document |

> `target_ids` contains `ART-NOTE-*` IDs. Each ID navigates to the corresponding note article inside a `SEC-NOTES-*` section. Unresolved note refs (0.2% — 2 refs) are genuine external appendix notes in a different PDF volume.

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

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `"APP-{div}-{letter}"` e.g. `"APP-B-C"` |
| `number` | `string` | Appendix letter |
| `title` | `string` | Appendix title |
| `sections` | `Section[]` | Sections using the same Article/Sentence/Clause hierarchy as regular Parts |
| `page_span` | `number[]` | |

> Appendix sections use the same full Article/Sentence/Clause/Subclause hierarchy as regular Part sections.

---

## 4. ID Naming Conventions

| Entity | Pattern | Example |
|---|---|---|
| Division | `DIV-{letter}` | `DIV-B` |
| Part | `PART-{div}-{n}` | `PART-B-4` |
| Section (numeric) | `SEC-{n}-{m}` | `SEC-4-1` |
| Notes Section | `SEC-NOTES-{part_id}` | `SEC-NOTES-PART-B-4` |
| Subsection | `SUBSEC-{n}-{m}-{k}` | `SUBSEC-4-1-6` |
| Article (numbered) | `ART-{n}-{m}-{k}-{j}` | `ART-4-1-6-5` |
| Article (unnumbered) | `ART-AUTO-{n}` | `ART-AUTO-153` |
| Note Article | `ART-NOTE-{A-num-safe}` | `ART-NOTE-A-4-1-1-3--1-` |
| Sentence | `SENT-{art_safe}-{n}` | `SENT-4-1-6-5-1` |
| Clause (lettered) | `CLAUSE-{art_safe}-{sent_n}-{letter}` | `CLAUSE-4-1-6-5-1-a` |
| Subclause (roman) | `SUBCLAUSE-{clause_id_safe}-{roman}` | `SUBCLAUSE-CLAUSE-4-1-6-5-1-a-i` |
| Table | `TBL-{n}` | `TBL-218` |
| Figure | `FIG-{n}` | `FIG-56` |
| Equation | `EQ-{n}` | `EQ-13` |
| Appendix | `APP-{div}-{letter}` | `APP-B-C` |
| Preface section | `PREF-SEC-{nn}` | `PREF-SEC-01` |
| Preface subsection | `PREF-SUBSEC-{nn}-{mm}` | `PREF-SUBSEC-01-02` |
| CF section | `CF-SEC-{nn}` | `CF-SEC-01` |

**ID construction rules:**
- Dots in article numbers → hyphens: `4.1.6.5` → `ART-4-1-6-5`
- For note articles: `.` `(` `)` → `-`: `A-4.1.1.3.(1)` → `ART-NOTE-A-4-1-1-3--1-`
- Subsections always use `SUBSEC-` not `SEC-`: `4.1.6` → `SUBSEC-4-1-6`

---

## 5. Document Tree — Full Hierarchy Diagram

```
Document
├── title, source_pdf, total_pages, _stats
│
├── preface
│   ├── id="PREFACE", title, page_span
│   └── sections[]  ← PrefaceSection[]
│       ├── id="PREF-SEC-01", number="", title, page_span
│       ├── content[]  ← ContentItem[]
│       └── subsections[]  ← PrefaceSubsection[]
│           ├── id="PREF-SUBSEC-01-02", number="", title, page_span
│           ├── content[], tables[], figures[], references[]
│
├── divisions[]  ← Division[]
│   ├── id="DIV-B", number, title, page_span
│   ├── parts[]  ← Part[]
│   │   ├── id="PART-B-4", number, title, page_span
│   │   └── sections[]  ← Section[]
│   │       │
│   │       ├── [Regular Section]  id="SEC-4-1"
│   │       │   ├── id, number, title, page_span
│   │       │   ├── subsections[]  ← Subsection[]
│   │       │   │   ├── id="SUBSEC-4-1-6", number, title, page_span
│   │       │   │   └── articles[]  ←── PRIMARY CONTENT
│   │       │   │       ├── id="ART-4-1-6-5", number, title, page_span
│   │       │   │       ├── sentences[]  ← Sentence[]
│   │       │   │       │   ├── id="SENT-4-1-6-5-1", number, marker, content
│   │       │   │       │   ├── clauses[]  ← Clause[]
│   │       │   │       │   │   ├── id="CLAUSE-4-1-6-5-1-a", number, marker, content
│   │       │   │       │   │   └── subclauses[]  ← Subclause[]
│   │       │   │       │   │       └── id="SUBCLAUSE-...-i", number, marker, content
│   │       │   │       │   ├── tables[], figures[], equations[], references[]
│   │       │   │       ├── content[]       ← always [] for regular articles
│   │       │   │       ├── tables[]        ← Table[] (see §3.9)
│   │       │   │       ├── figures[]       ← Figure[] (see §3.10)
│   │       │   │       ├── equations[]     ← Equation[] (see §3.11)
│   │       │   │       ├── references[]    ← Reference[] (see §3.12)
│   │       │   │       └── note_refs[]     ← NoteRef[] (see §3.13)
│   │       │   └── articles[]   ← direct section articles (uncommon)
│   │       │
│   │       └── [Notes Section]  id="SEC-NOTES-PART-B-4"
│   │           ├── id, number="", title, page_span
│   │           ├── subsections[]  ← always []
│   │           └── articles[]  ← NoteArticle[] (direct, no subsection nesting)
│   │               ├── id="ART-NOTE-A-4-1-1-3--1-", number="A-4.1.1.3.(1)"
│   │               ├── sentences[]  ← always []
│   │               ├── content[]    ← ContentItem[] (note text here)
│   │               ├── tables[], figures[], equations[]
│   │               ├── references[], note_refs[]
│   │
│   └── appendices[]  ← Appendix[]
│       ├── id="APP-B-C", number, title, page_span
│       └── sections[]  (same structure as Regular Section above)
│
└── conversion_factors
    ├── id="CONVERSION-FACTORS", title, page_span
    └── sections[]  ← ConversionSection[]
        ├── id="CF-SEC-01", number="", title, page_span
        ├── content[]  ← ContentItem[]
        ├── tables[]   ← Table[]
        └── figures[]  ← Figure[]
```

---

## 6. Full Reference Linking Schema

This section describes the complete pipeline by which cross-references and note references are extracted, resolved, and embedded in the JSON.

### 6.1 Standard Cross-Reference Pipeline

**Extraction** — `reference_linker.py` scans the text content of every Article, Sentence, Clause, and Subclause using regex patterns that detect:

| Kind | Pattern example | Example match |
|---|---|---|
| Sentence | `Sentence 4.1.6.5.(1)` | number: `4.1.6.5.(1)` |
| Article | `Article 4.1.6.5.` | number: `4.1.6.5` |
| Subsection | `Subsection 4.1.6.` | number: `4.1.6` |
| Section | `Section 4.1.` | number: `4.1` |
| Clause | `Clause 4.1.6.5.` | number: `4.1.6.5` |
| Table | `Table 4.1.5.3.-A` | number: `4.1.5.3.-A` |
| Figure | `Figure 4.1.6.5.-A` | number: `4.1.6.5.-A` |

**Resolution** — `_ref_to_id()` converts each (kind, number) pair to a document node ID:

| Kind | ID construction | Fallback |
|---|---|---|
| Sentence / Article / Clause | `SENT-` / `ART-` / `ART-` | title-number index for unnumbered articles |
| Subsection | `SUBSEC-{n}-{m}-{k}` | `SEC-` → `ART-` → `CL-` |
| Section | `SEC-{n}-{m}` | `ART-` → `CL-` |
| Table | Caption lookup (exact then fuzzy) | `TBL-{normalized}` |
| Figure | `reference_key` exact lookup then fuzzy | `FIG-{normalized}` |

**Figure resolution uses a two-step lookup:**
1. Exact: `_cap_Figure {number}` key → `FIG-*` node (fast path)
2. Fuzzy: normalize (strip dots/hyphens/case) → compare against all `FIG-*` caption keys

Figure and Table lookups are type-guarded — figure queries only match `FIG-*` nodes, table queries only match `TBL-*` nodes. There is no cross-type collision.

**Deduplication** — Per-clause, references are deduplicated by `(kind, ref)` tuple. The same reference appearing multiple times in one article is stored once.

**Result** — Each reference entry stored on the node:

```json
{
  "text":      "Figure 4.1.6.5.-A",
  "kind":      "Figure",
  "number":    "4.1.6.5.-A",
  "target_id": "FIG-55",
  "resolved":  true,
  "lookup_key": "Figure 4.1.6.5.-A"
}
```

(`lookup_key` present only on Figure-kind references.)

### 6.2 Table Caption and Cell Reference Pipeline

Tables go through a separate enrichment step (`_enrich_tables_in_dict`) that:

1. Parses the raw caption string into a `TableCaption` object (§3.9.2) — extracts `table_number` (with trailing dot), `table_label`, `title`, and `forming_part_of`.
2. Converts raw header list to indexed `Header[]` objects.
3. Converts raw row list to structured `Row[]` with `Cell[]` objects, running `_extract_cell_refs()` on every cell's text.
4. Builds a deduplicated `table.references[]` from caption forming_part_of + all cell refs.
5. Resolves all `target_id` / `resolved` fields via `_link_table_references()`.

**Cell reference extraction** uses the same regex patterns as prose reference extraction. Cell references carry the same `(text, kind, number, target_id, resolved)` fields plus a `source` field.

### 6.3 Appendix Note Reference Pipeline

Note references (`See Note A-...`) are extracted by `RE_NOTE` pattern and resolved against a note index built from three sources:

| Source | Coverage |
|---|---|
| `ART-NOTE-*` article `number` field | Primary — all `A-`-numbered note articles |
| `ART-AUTO-*` article `title` starting with `A-` | Legacy path for old-format notes |
| First line of `content[]` items starting with `A-` | Embedded sub-notes within larger note articles |

Resolution is exact-match first, then base-match (strip sentence sub-number). Multiple note articles may resolve to the same note ref (stored as `target_ids[]` array).

**Stats:** 920/922 resolved (99.8%). The 2 unresolved note refs are genuine external appendix notes in a different BCBC volume.

---

## 7. API Endpoints (port 8000)

The FastAPI backend exposes the document for frontend consumption:

| Method | Path | Returns |
|---|---|---|
| `GET` | `/` | Health check `{"status": "ok"}` |
| `GET` | `/document` | Full document tree (~43.6 MB) |
| `GET` | `/document/summary` | Lightweight nav tree (parts + section article counts, no clause content) |
| `GET` | `/section/{section_id}` | Single section with all its articles |
| `GET` | `/clause/{clause_id}` | Single article + `_breadcrumb` context — accepts `ART-*` IDs |
| `GET` | `/search?q={term}` | Full-text search (max 50 results, snippet 60 chars before + 100 after match) |
| `GET` | `/references/{node_id}` | Reverse lookup: which articles reference this node |

**CORS** is configured for `http://localhost:8501` and `http://127.0.0.1:8501` (Streamlit). Update to port 3000 if adding a React/Next.js frontend.

---

## 8. Frontend Rendering Guidance

### 8.1 Legal Text Rendering

The legal text is structured as a proper hierarchy — do **not** attempt to render it as a flat list:

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

### 8.2 Table Rendering

```typescript
function renderTable(table: Table) {
  // 1. Display caption
  const label = table.caption.table_label;   // e.g. "Table 4.1.5.3."
  const title = table.caption.title;          // descriptive text (no leading dot)

  // 2. Optional "Forming Part of" link
  const fp = table.caption.forming_part_of;
  if (fp && fp.resolved) {
    // render link to fp.target_id
  }

  // 3. Column headers
  const headers = table.headers.map(h => h.text);

  // 4. Data rows with inline reference links
  for (const row of table.rows) {
    for (const cell of row.cells) {
      // render cell.value as text
      // overlay cell.references where resolved: true as inline hyperlinks
    }
  }

  // 5. Optional "Referenced Provisions" panel
  const captionRefs = table.references.filter(r => r.source === "caption");
  const cellRefs    = table.references.filter(r => r.source === "cell" && r.resolved);
}
```

### 8.3 Figure Rendering

```typescript
function renderFigure(figure: Figure) {
  // 1. Build image URL from image_key (not image_path)
  const imageUrl = `/figures/${figure.image_key}`;

  // 2. Display structured caption
  const label = figure.caption.figure_label;  // e.g. "Figure 4.1.6.5.-A"
  const title = figure.caption.title;          // descriptive text (may be "")
  const raw   = figure.caption.raw;            // full original caption

  // 3. Accessibility
  // Always render alt_text for screen readers

  // 4. Hyperlink matching — use reference_key
  // When building a figure lookup index:
  //   index[figure.reference_key] = figure.id;
  // When resolving a reference with kind="Figure":
  //   const figId = index[ref.lookup_key] ?? ref.target_id;
}
```

### 8.4 Math Rendering

- **Inline math** in `content` strings (Sentence / Clause / Subclause): delimited by `$...$` → render with KaTeX inline mode.
- **Block equations** in `Equation` objects: use the `latex` field → render with KaTeX `\displaystyle` or MathJax `\[ ... \]` block mode.
- **Table cell math**: cells may contain LaTeX notation (e.g. `\beta`, `\frac{x}{y}`). Detect `\` in cell text and render accordingly.

### 8.5 Reference / Link Rendering

```typescript
function renderReference(ref: Reference) {
  if (!ref.resolved) {
    // External reference — render as styled badge, not a clickable link
    return <Badge>{ref.text}</Badge>;
  }
  // Internal reference — render as hyperlink
  // Navigate to the node identified by ref.target_id
  return <Link to={`/${ref.target_id}`}>{ref.text}</Link>;
}

function renderNoteRef(nr: NoteRef) {
  if (!nr.resolved) {
    return <Badge>{nr.note_ref}</Badge>;
  }
  // May have multiple target_ids — link to first, list all
  return nr.target_ids.map(id => <Link to={`/${id}`}>{nr.note_ref}</Link>);
}
```

### 8.6 Traversal Pattern

```typescript
// Complete traversal of all articles
for (const division of doc.divisions) {
  for (const part of division.parts) {
    for (const section of part.sections) {

      if (section.id.startsWith("SEC-NOTES-")) {
        // Notes section — articles are direct children
        // Note articles use content[], not sentences[]
        for (const article of section.articles) {
          renderNoteArticle(article);
        }
      } else {
        // Regular section
        for (const subsection of section.subsections) {
          for (const article of subsection.articles) {
            renderArticle(article);
          }
        }
        // Also check direct section articles (uncommon)
        for (const article of section.articles) {
          renderArticle(article);
        }
      }
    }
  }
  // Appendices follow same structure as regular sections
  for (const appendix of division.appendices) {
    for (const section of appendix.sections) {
      for (const subsection of section.subsections) {
        for (const article of subsection.articles) {
          renderArticle(article);
        }
      }
    }
  }
}
```

### 8.7 Article vs Note Article

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
    // Article-level tables, figures, equations
    for (const tbl of article.tables)   renderTable(tbl);
    for (const fig of article.figures)  renderFigure(fig);
    for (const eq of article.equations) renderEquation(eq);
  }
}
```

---

## 9. Key Schema Changes vs Previous Version

This section summarizes the breaking changes introduced in the 2026-04-11 regeneration. Any frontend code targeting the previous JSON must be updated.

| Area | Previous | Current | Action Required |
|---|---|---|---|
| **Reference resolution rate** | 84.7% (2,495/2,945) | 97.4% (2,867/2,945) | No action — more refs now resolve |
| **Subsection `target_id` prefix** | `SEC-*` (e.g. `SEC-9-10-9`) | `SUBSEC-*` (e.g. `SUBSEC-9-10-9`) | **Update** any frontend logic that navigates by subsection `target_id` — look up `SUBSEC-*` node, not `SEC-*` |
| **`table.caption` type** | `string` | `TableCaption` object | **Update** — read `caption.raw`, `caption.title`, `caption.table_label`, `caption.table_number` instead of the string directly |
| **`table.caption.table_number`** | `"4.1.5.3"` (dot stripped) | `"4.1.5.3."` (trailing dot preserved) | **Update** — use `caption.table_label` for display; do not add/strip the dot manually |
| **`table.caption.title`** | May start with `"."` | Never starts with `"."` | No action — fix was applied in parser |
| **`figure.caption` type** | `string` | `FigureCaption` object | **Update** — read `caption.raw`, `caption.figure_label`, `caption.figure_number`, `caption.title` |
| **`figure.reference_key`** | Not present | `string` — canonical match key | **Use** for figure lookup index construction |
| **`figure.page_span`** | Not present | `number[]` | Available for multi-page figures |
| **Clause-level `reference.number`** | Not present | `string` | Available — extracted numeric identifier |
| **Figure `reference.lookup_key`** | Not present | `string` — `"Figure {number}"` | **Use** instead of `reference.text` for figure resolution |
| **`table.headers` type** | `string[]` | `Header[]` objects `{ index, text }` | **Update** — read `header.text` not the string directly |
| **`table.rows` type** | `string[][]` | `Row[]` objects with `cells[]` | **Update** — read `row.cells[i].value` not `row[i]` |
