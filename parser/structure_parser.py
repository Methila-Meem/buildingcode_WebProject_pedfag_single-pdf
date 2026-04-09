"""
parser/structure_parser.py
===========================
Parses Datalab Marker API JSON output into a structured BCBC 2024 document tree.

OUTPUT SCHEMA
=============
Top-level keys (in order):
    title, source_pdf, total_pages, preface, divisions, conversion_factors

Hierarchy:
    Preface  -> sections (PrefaceSection) -> subsections (PrefaceSubsection)
    Division -> parts   (Part)            -> sections   (Section)
             -> appendices (Appendix)        -> subsections (Subsection)
                                              -> clauses    (Clause)
    ConversionFactors -> sections (ConversionFactorsSection)

BCBC Numbering System
=====================
    4          -> Part
    4.1        -> Section
    4.1.1      -> Subsection
    4.1.1.3    -> Clause/Article
    4.1.1.3.(2)-> Sentence (stays inside clause.content)
    (a) / a)   -> sub_clause marker (inside clause.content)

ID Conventions
==============
    DIV-A          Division A
    PART-A-1       Division A, Part 1
    SEC-4-1        Section 4.1
    SUBSEC-4-1-1   Subsection 4.1.1
    CL-4-1-1-3     Clause 4.1.1.3
    CL-AUTO-N      Unnumbered clause
    PREFACE        Preface object
    PREF-SEC-01    Preface Section 1
    PREF-SUBSEC-01-02  Preface Section 1, Subsection 2
    CONVERSION-FACTORS  Conversion Factors object
    CF-SEC-01      Conversion Factors Section 1
    APP-B-C        Division B, Appendix C
"""

import re
import os
import base64
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any
from datetime import datetime


# =============================================================================
# Data models
# =============================================================================

@dataclass
class ContentItem:
    """
    One item in the ordered content sequence of a Clause or Preface section.
    type: "text" | "equation" | "figure" | "table" | "sub_clause"
    """
    type: str
    value: str = ""
    latex: str = ""
    figure_id: str = ""
    image_key: str = ""
    image_path: str = ""
    caption: str = ""
    alt_text: str = ""
    table_id: str = ""
    marker: str = ""


@dataclass
class Table:
    id: str
    caption: str
    headers: List[str]
    rows: List[List[str]]
    page: int = 0


@dataclass
class Figure:
    id: str
    caption: str
    alt_text: str
    image_key: str
    image_path: str
    page: int = 0


@dataclass
class Equation:
    id: str
    latex: str
    page: int = 0


@dataclass
class Clause:
    id: str
    number: str
    title: str
    content: List[ContentItem] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    equations: List[Equation] = field(default_factory=list)
    references: List[dict] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)
    # note_refs is added dynamically by reference_linker


@dataclass
class Subsection:
    """Maps to 3-part numbers: 4.1.1"""
    id: str
    number: str
    title: str
    clauses: List[Clause] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class Section:
    """Maps to 2-part numbers: 4.1"""
    id: str
    number: str
    title: str
    subsections: List[Subsection] = field(default_factory=list)
    clauses: List[Clause] = field(default_factory=list)   # fallback direct clauses
    page_span: List[int] = field(default_factory=list)


@dataclass
class Part:
    """Maps to 1-part numbers: 4 (Part 4)"""
    id: str
    number: str
    title: str
    sections: List[Section] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class Appendix:
    """Appendix under a Division (e.g. Appendix C, Appendix D)"""
    id: str
    number: str
    title: str
    sections: List[Section] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class Division:
    """Division A, B, or C"""
    id: str
    number: str
    title: str
    parts: List[Part] = field(default_factory=list)
    appendices: List[Appendix] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class PrefaceSubsection:
    """A subsection within a Preface section (unnumbered)"""
    id: str
    number: str
    title: str
    content: List[ContentItem] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    references: List[dict] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class PrefaceSection:
    """A top-level section within the Preface (unnumbered)"""
    id: str
    number: str
    title: str
    content: List[ContentItem] = field(default_factory=list)
    subsections: List[PrefaceSubsection] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class Preface:
    id: str = "PREFACE"
    title: str = "Preface"
    sections: List[PrefaceSection] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class ConversionFactorsSection:
    """A section within the Conversion Factors appendix"""
    id: str
    number: str
    title: str
    content: List[ContentItem] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class ConversionFactors:
    id: str = "CONVERSION-FACTORS"
    title: str = "Conversion Factors"
    sections: List[ConversionFactorsSection] = field(default_factory=list)
    page_span: List[int] = field(default_factory=list)


@dataclass
class Document:
    title: str
    source_pdf: str
    total_pages: int
    preface: Preface = field(default_factory=Preface)
    divisions: List[Division] = field(default_factory=list)
    conversion_factors: ConversionFactors = field(default_factory=ConversionFactors)


# =============================================================================
# Regex patterns
# =============================================================================

# Structural heading patterns
RE_DIVISION   = re.compile(r'^Division\s+([A-C])\b\s*[:\-–—]?\s*(.*)', re.IGNORECASE)
RE_APPENDIX   = re.compile(r'^Appendix\s+([A-Za-z])\b\s*(.*)',          re.IGNORECASE)
RE_PREFACE    = re.compile(r'^\s*Preface\s*$',                           re.IGNORECASE)
RE_CONVERSION = re.compile(r'^\s*Conversion\s+Factors\s*$',              re.IGNORECASE)

# Numbering hierarchy
RE_PART     = re.compile(r'^Part\s*(\d+)\s*(.*)',                    re.IGNORECASE)
RE_SECTION  = re.compile(r'^(?:Section\s+)?(\d+\.\d+)\.?\s*(.*)',    re.IGNORECASE)
RE_ARTICLE  = re.compile(r'^(\d+\.\d+\.\d+)\.?\s*(.*)')
RE_SENTENCE = re.compile(r'^(\d+\.\d+\.\d+\.\d+)\.?\s*(.*)')        # check before RE_ARTICLE

# Sub-clause markers: (a), a), i., etc.
RE_SUBCLAUSE = re.compile(r'^\s*(\([a-z]+\)|[a-z]\)|[ivxlcdm]+\.)\s+(.+)', re.IGNORECASE)

# Figure caption number extraction
RE_FIGURE_NUM = re.compile(r'Figure\s+([\d\.]+[\w\.\-]*)', re.IGNORECASE)

# Notes to Part heading and note clause number
RE_NOTES_PART = re.compile(r'^Notes\s+to\s+Part\s*(\d+)\s*(.*)', re.IGNORECASE)
RE_NOTE_CLAUSE = re.compile(
    r'^(A-(?:Table\s+)?[\d]+(?:\.[\d]+)*\.?(?:\(\d+\))?\.?)\s+(.*)',
    re.DOTALL | re.IGNORECASE
)


# =============================================================================
# HTML helpers  (unchanged from previous version)
# =============================================================================

def strip_html(html: str) -> str:
    """Remove HTML tags, decode entities, normalise whitespace."""
    if not html:
        return ""
    text = re.sub(r'<\s*/?\s*[A-Za-z][^>]*>', ' ', html)
    text = (text
            .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"'))
    return re.sub(r'\s+', ' ', text).strip()


_INLINE_MATH_SPLIT = re.compile(
    r'(<math[^>]*>.*?</math>)',
    re.DOTALL | re.IGNORECASE
)


def _strip_html_keep_text(html: str) -> str:
    """Strip all HTML tags except <math> markers."""
    text = re.sub(r'<\s*/?\s*(?!math)[A-Za-z][^>]*>', ' ', html)
    text = (text
            .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"'))
    return re.sub(r'\s+', ' ', text).strip()


def inline_math_to_markdown(html: str) -> str:
    """Convert inline <math> tags to $...$ notation, strip remaining HTML."""
    def _clean_latex(inner: str) -> str:
        latex = inner.strip()
        latex = latex.replace('\\\\', '\\')
        latex = (latex.replace('&amp;', '&').replace('&lt;', '<')
                 .replace('&gt;', '>').replace('&nbsp;', ' '))
        return re.sub(r'\s+', ' ', latex).strip()

    result = re.sub(
        r'<math[^>]*>(.*?)</math>',
        lambda m: f'${_clean_latex(m.group(1))}$',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    result = re.sub(r'<\s*/?\s*[A-Za-z][^>]*>', ' ', result)
    result = (result
              .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
              .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"'))
    return re.sub(r'\s+', ' ', result).strip()


def split_inline_math(html: str) -> list:
    """Legacy shim — returns single-item list with markdown string."""
    value = inline_math_to_markdown(html)
    if value:
        return [{"type": "text", "value": value}]
    return []


def extract_math(html: str) -> list:
    """Return list of LaTeX strings, one per <math> tag."""
    raw_parts = re.findall(r'<math[^>]*>(.*?)</math>', html,
                           re.DOTALL | re.IGNORECASE)
    result = []
    for p in raw_parts:
        latex = p.strip().replace('\\\\', '\\')
        latex = (latex.replace('&amp;', '&').replace('&lt;', '<')
                 .replace('&gt;', '>').replace('&nbsp;', ' '))
        latex = re.sub(r'\s+', ' ', latex).strip()
        if latex:
            result.append(latex)
    return result


def parse_heading(html: str):
    """Extract (level, plain_text) from a SectionHeader HTML block."""
    m = re.match(r'<h(\d)[^>]*>(.*?)</h\1>', html.strip(), re.DOTALL | re.IGNORECASE)
    if m:
        return int(m.group(1)), strip_html(m.group(2))
    return 0, strip_html(html)


def listgroup_to_lines(html: str) -> str:
    """Convert ListGroup HTML to newline-separated lines, preserving inline math."""
    text_with_newlines = re.sub(r'</li>', '\n', html, flags=re.IGNORECASE)
    lines = []
    for raw_line in text_with_newlines.splitlines():
        if re.search(r'<math', raw_line, re.IGNORECASE):
            line = inline_math_to_markdown(raw_line)
        else:
            line = re.sub(r'<[^>]+>', '', raw_line)
            line = (line.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"'))
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if line:
            lines.append(line)
    return '\n'.join(lines)


def parse_table_html(html: str):
    """
    Parse HTML table into (headers, rows) with rowspan/colspan handling.
    Multi-row <thead> is collapsed into column names with ' / ' separators.
    """
    headers: list = []

    thead = re.search(r'<thead[^>]*>(.*?)</thead>', html, re.DOTALL | re.IGNORECASE)
    if thead:
        thead_html   = thead.group(1)
        header_rows  = re.findall(r'<tr[^>]*>(.*?)</tr>', thead_html,
                                  re.DOTALL | re.IGNORECASE)

        if len(header_rows) <= 1:
            ths     = re.findall(r'<th[^>]*>(.*?)</th>', thead_html,
                                  re.DOTALL | re.IGNORECASE)
            headers = [
                inline_math_to_markdown(th) if re.search(r'<math', th, re.IGNORECASE)
                else strip_html(th)
                for th in ths
            ]
        else:
            first_ths = re.findall(r'<th([^>]*)>(.*?)</th>', header_rows[0],
                                   re.DOTALL | re.IGNORECASE)
            num_cols = 0
            for attrs, _ in first_ths:
                cs = re.search(r'colspan=["\'](\d+)["\']', attrs)
                num_cols += int(cs.group(1)) if cs else 1

            n_rows     = len(header_rows)
            label_grid = [[''] * num_cols for _ in range(n_rows)]
            th_carry   = {}
            row_new_cells: list = [[] for _ in range(n_rows)]

            for row_i, tr_html in enumerate(header_rows):
                th_matches = re.findall(r'<th([^>]*)>(.*?)</th>', tr_html,
                                        re.DOTALL | re.IGNORECASE)
                th_iter = iter(th_matches)
                col     = 0

                while col < num_cols:
                    if col in th_carry:
                        remaining, label = th_carry[col]
                        label_grid[row_i][col] = label
                        if remaining - 1 > 0:
                            th_carry[col] = (remaining - 1, label)
                        else:
                            del th_carry[col]
                        col += 1
                        continue

                    try:
                        attrs, cell_html = next(th_iter)
                    except StopIteration:
                        col += 1
                        continue

                    if re.search(r'<math', cell_html, re.IGNORECASE):
                        label = inline_math_to_markdown(cell_html)
                    else:
                        label = strip_html(cell_html)

                    rs      = re.search(r'rowspan=["\'](\d+)["\']', attrs)
                    cs      = re.search(r'colspan=["\'](\d+)["\']', attrs)
                    rowspan = int(rs.group(1)) if rs else 1
                    colspan = int(cs.group(1)) if cs else 1

                    for c in range(colspan):
                        if col + c < num_cols:
                            label_grid[row_i][col + c] = label

                    if rowspan > 1:
                        for c in range(colspan):
                            if col + c < num_cols:
                                th_carry[col + c] = (rowspan - 1, label)

                    row_new_cells[row_i].append((col, colspan, label))
                    col += colspan

            spanning_rows: set = set()
            for row_i in range(n_rows):
                if row_i == n_rows - 1:
                    continue
                new = row_new_cells[row_i]
                if len(new) == 1 and new[0][1] > 1:
                    spanning_rows.add(row_i)

            headers = []
            seen_names: dict = {}
            for col in range(num_cols):
                parts = []
                for row_i in range(n_rows):
                    lbl = label_grid[row_i][col].strip()
                    if not lbl:
                        continue
                    if parts and parts[-1] == lbl:
                        continue
                    if (col == 0
                            and row_i == n_rows - 1 and parts
                            and len(lbl) <= 4
                            and re.match(r'^[0-9A-Z]+$', lbl)
                            and len(parts[-1]) > len(lbl) + 2):
                        continue
                    parts.append(lbl)
                name = ' / '.join(parts) if parts else f"Col {col+1}"
                if name in seen_names:
                    seen_names[name] += 1
                    name = f"{name} ({seen_names[name]})"
                else:
                    seen_names[name] = 1
                headers.append(name)

    num_cols = len(headers) if headers else 2

    rows: list = []
    tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL | re.IGNORECASE)
    if not tbody:
        return headers, rows

    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL | re.IGNORECASE)
    rowspan_carry = {}

    for tr in trs:
        td_matches = re.findall(r'<td([^>]*)>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
        row     = [''] * num_cols
        td_iter = iter(td_matches)
        col     = 0

        while col < num_cols:
            if col in rowspan_carry:
                remaining, value = rowspan_carry[col]
                row[col] = value
                if remaining - 1 > 0:
                    rowspan_carry[col] = (remaining - 1, value)
                else:
                    del rowspan_carry[col]
                col += 1
                continue

            try:
                attrs_str, cell_html = next(td_iter)
            except StopIteration:
                col += 1
                continue

            cell_value = strip_html(cell_html)
            rs = re.search(r'rowspan=["\'](\d+)["\']', attrs_str)
            cs = re.search(r'colspan=["\'](\d+)["\']', attrs_str)
            rowspan = int(rs.group(1)) if rs else 1
            colspan = int(cs.group(1)) if cs else 1

            if colspan >= num_cols:
                row[0] = cell_value
            else:
                for c in range(colspan):
                    if col + c < num_cols:
                        row[col + c] = cell_value

            if rowspan > 1:
                for c in range(min(colspan, num_cols)):
                    if col + c < num_cols:
                        rowspan_carry[col + c] = (rowspan - 1, cell_value)

            col += colspan

        if any(c.strip() for c in row):
            rows.append(row)

    # bbox-based carry for empty cells
    row_bboxes: list = []
    trs_all = re.findall(r'<tr[^>]*>(.*?)</tr>',
                         (tbody.group(1) if tbody else ""),
                         re.DOTALL | re.IGNORECASE)

    for tr in trs_all:
        td_matches = re.findall(r'<td([^>]*)>', tr, re.IGNORECASE)
        if len(td_matches) < 2:
            continue
        use_attrs  = td_matches[0]
        load_attrs = td_matches[1]

        def _y(attrs_str, coord_idx):
            m = re.search(r'data-bbox=["\']([^"\']+)["\']', attrs_str)
            if not m:
                return None
            parts = m.group(1).split()
            return int(parts[coord_idx]) if len(parts) == 4 else None

        use_y1   = _y(use_attrs,  1)
        load_y2  = _y(load_attrs, 3)

        td_content = re.findall(r'<td[^>]*>(.*?)</td>', tr,
                                re.DOTALL | re.IGNORECASE)
        row_texts = [re.sub(r'<[^>]+>', '', c).strip() for c in td_content]
        if any(t for t in row_texts):
            row_bboxes.append((use_y1, load_y2))

    if row_bboxes and len(row_bboxes) == len(rows):
        col_last_val  = {}
        col_last_y2   = {}

        for row_i, (row, (use_y1, load_y2)) in enumerate(zip(rows, row_bboxes)):
            for col_idx in range(len(row)):
                val = row[col_idx]
                if val.strip():
                    col_last_val[col_idx] = val
                    if load_y2 is not None:
                        col_last_y2[col_idx] = load_y2
                else:
                    if (col_idx in col_last_val
                            and col_idx in col_last_y2
                            and use_y1 is not None
                            and col_last_y2[col_idx] > use_y1):
                        rows[row_i][col_idx] = col_last_val[col_idx]

    return headers, rows


def extract_alt_text(html: str) -> str:
    """Extract alt attribute from <img> tag."""
    m = re.search(r'<img[^>]+alt=["\']([^"\']*)["\']', html, re.IGNORECASE)
    return m.group(1).strip() if m else strip_html(html)


def save_image(image_key: str, base64_data: str, figures_dir: str) -> str:
    """Decode base64 image and save to disk. Returns relative path."""
    os.makedirs(figures_dir, exist_ok=True)
    file_path = os.path.join(figures_dir, image_key)
    if not os.path.exists(file_path):
        try:
            img_bytes = base64.b64decode(base64_data)
            with open(file_path, 'wb') as f:
                f.write(img_bytes)
        except Exception as e:
            print(f"[Parser] Warning: could not save image {image_key}: {e}")
            return ""
    return os.path.join("storage", "figures", image_key)


# =============================================================================
# Main parser
# =============================================================================

class StructureParser:

    def __init__(self, source_pdf: str = "unknown.pdf",
                 figures_dir: str = "storage/figures"):
        self.source_pdf  = source_pdf
        self.figures_dir = figures_dir

        # Counters
        self._auto_clause_counter    = 0
        self._table_counter          = 0
        self._equation_counter       = 0
        self._figure_counter         = 0
        self._preface_sec_counter    = 0
        self._preface_subsec_counter = 0   # resets per section
        self._cf_sec_counter         = 0

        # Internal indexes (populated during parsing)
        self._images_dict     = {}   # image_key -> base64 from Datalab result
        self._page_objects    = []   # raw page list for section_hierarchy lookup
        self._clause_index    = {}   # clause_id -> Clause
        self._subsec_index    = {}   # subsec_id -> Subsection
        self._section_index   = {}   # sec_id    -> Section
        self._notes_section_index = {}   # "SEC-NOTES-{part_id}" -> Section

    def parse(self, datalab_result: dict) -> Document:
        self._images_dict  = datalab_result.get("images") or {}
        self._page_objects = (datalab_result.get("json") or {}).get("children", [])
        blocks     = self._flatten_blocks(datalab_result)
        total_pages = (
            datalab_result.get("page_count") or
            len((datalab_result.get("json") or {}).get("children", []))
        )
        document = Document(
            title=self._detect_title(blocks),
            source_pdf=self.source_pdf,
            total_pages=total_pages or 0,
        )
        preface, divisions, conversion_factors = self._build_hierarchy(blocks)
        document.preface           = preface
        document.divisions         = divisions
        document.conversion_factors = conversion_factors
        return document

    # -------------------------------------------------------------------------
    # Block flattening  (unchanged logic — only stores raw block for hr detection)
    # -------------------------------------------------------------------------

    def _flatten_blocks(self, datalab_result: dict) -> list:
        """Flatten Datalab JSON pages into an ordered block list."""
        flat = []
        json_output  = datalab_result.get("json") or {}
        page_objects = json_output.get("children", [])

        if not page_objects:
            return self._flatten_legacy(datalab_result)

        for page_obj in page_objects:
            if page_obj.get("block_type") != "Page":
                continue
            try:
                page_num = int(page_obj["id"].split("/page/")[1].split("/")[0]) + 1
            except (IndexError, ValueError, KeyError):
                page_num = 1

            children = page_obj.get("children", [])

            for idx, block in enumerate(children):
                btype_raw = block.get("block_type", "")
                html      = (block.get("html") or "").strip()

                if btype_raw in ("PageFooter", "PageHeader",
                                 "TableOfContents", "Footnote"):
                    continue
                if not html:
                    continue

                if btype_raw == "SectionHeader":
                    level, text = parse_heading(html)
                    # Detect horizontal rule in the raw HTML — content headings
                    # in BCBC use <hr/> as a section break; TOC entries don't.
                    has_hr = bool(re.search(r'<hr', html, re.IGNORECASE))
                    flat.append({"type": "heading", "level": level,
                                 "text": text, "page": page_num,
                                 "raw": block, "has_hr": has_hr})

                elif btype_raw == "ListGroup":
                    text = listgroup_to_lines(html)
                    if text:
                        flat.append({"type": "text", "level": 0,
                                     "text": text, "page": page_num, "raw": block})

                elif btype_raw == "Equation":
                    latex_list = extract_math(html)
                    if not latex_list:
                        text_fb = strip_html(html)
                        if text_fb:
                            latex_list = [text_fb]
                    for latex in latex_list:
                        flat.append({"type": "equation", "level": 0,
                                     "text": latex, "latex": latex,
                                     "page": page_num, "raw": block})

                elif btype_raw in ("Figure", "Picture"):
                    block_images = block.get("images") or {}
                    image_key    = next(iter(block_images.keys()), "")
                    alt_text     = extract_alt_text(html)

                    alt_lower = alt_text.lower().strip()
                    if alt_lower in ("horizontal line", "vertical line",
                                     "divider", "line", "rule", "separator"):
                        continue

                    caption = self._find_figure_caption(children, idx, alt_text)
                    flat.append({"type": "figure", "level": 0,
                                 "text": alt_text, "image_key": image_key,
                                 "alt_text": alt_text, "caption": caption,
                                 "page": page_num, "raw": block})

                elif btype_raw == "Caption":
                    if re.search(r'<math', html, re.IGNORECASE):
                        text = inline_math_to_markdown(html)
                    else:
                        text = strip_html(html)
                    if text:
                        flat.append({"type": "caption", "level": 0,
                                     "text": text, "page": page_num, "raw": block})

                elif btype_raw == "Table":
                    flat.append({"type": "table", "level": 0,
                                 "text": html, "page": page_num, "raw": block})

                else:
                    if re.search(r'<math', html, re.IGNORECASE):
                        flat.append({"type": "text", "level": 0,
                                     "text": html, "has_inline_math": True,
                                     "page": page_num, "raw": block})
                    else:
                        text = strip_html(html)
                        if text:
                            flat.append({"type": "text", "level": 0,
                                         "text": text, "page": page_num,
                                         "raw": block})

        return flat

    def _find_figure_caption(self, siblings: list, fig_idx: int,
                              alt_text: str) -> str:
        """Find caption for a Figure block using bidirectional search."""
        if fig_idx > 0:
            prev = siblings[fig_idx - 1]
            if prev.get("block_type") == "Caption":
                return strip_html(prev.get("html", ""))

        if fig_idx < len(siblings) - 1:
            nxt = siblings[fig_idx + 1]
            if nxt.get("block_type") == "Caption":
                return strip_html(nxt.get("html", ""))
            if nxt.get("block_type") == "SectionHeader":
                m = re.search(r'Notes to (Figure\s+[\w\.\-]+)',
                              nxt.get("html", ""), re.IGNORECASE)
                if m:
                    return m.group(1)

        m = RE_FIGURE_NUM.search(alt_text)
        if m:
            return f"Figure {m.group(1)}"
        return ""

    def _flatten_legacy(self, datalab_result: dict) -> list:
        """Fallback for old API format or markdown-only responses."""
        flat = []
        for page_num, page in enumerate(
                datalab_result.get("pages", []), start=1):
            for block in page.get("blocks", []):
                flat.append({
                    "type":  block.get("block_type", "text"),
                    "text":  block.get("html", block.get("text", "")).strip(),
                    "level": block.get("level", 0),
                    "page":  page_num, "raw": block,
                })
        if not flat and datalab_result.get("markdown"):
            for line in datalab_result["markdown"].splitlines():
                s = line.strip()
                if not s:
                    continue
                for prefix, lvl in [("#### ",4),("### ",3),("## ",2),("# ",1)]:
                    if s.startswith(prefix):
                        flat.append({"type":"heading","level":lvl,
                                     "text":s[len(prefix):],"page":1,"raw":{}})
                        break
                else:
                    flat.append({"type":"text","level":0,"text":s,"page":1,"raw":{}})
        return flat

    # -------------------------------------------------------------------------
    # Title detection
    # -------------------------------------------------------------------------

    def _detect_title(self, blocks: list) -> str:
        for b in blocks:
            if b["type"] == "heading" and b.get("level", 0) == 1:
                return b["text"]
        return "British Columbia Building Code 2024"

    # -------------------------------------------------------------------------
    # Main hierarchy builder
    # -------------------------------------------------------------------------

    def _build_hierarchy(self, blocks: list):
        """
        Walk all blocks in order and build:
            Preface / Division[A,B,C] / ConversionFactors

        Returns:
            (preface, divisions, conversion_factors)

        Mode tracking:
            "init"               — before any structural heading
            "preface"            — inside Preface
            "normal"             — inside a Division (main code content)
            "appendix"           — inside a Division appendix
            "conversion_factors" — inside Conversion Factors
        """
        preface           = Preface()
        divisions: List[Division] = []
        conversion_factors = ConversionFactors()

        # Current context
        mode: str                    = "init"
        current_division: Optional[Division]               = None
        current_part:     Optional[Part]                   = None
        current_section:  Optional[Section]                = None
        current_subsection: Optional[Subsection]           = None
        current_clause:   Optional[Clause]                 = None
        current_appendix: Optional[Appendix]               = None
        current_pref_sec: Optional[PrefaceSection]         = None
        current_pref_subsec: Optional[PrefaceSubsection]   = None
        current_cf_sec:   Optional[ConversionFactorsSection] = None
        current_notes_section: Optional[Section] = None
        current_note_clause:   Optional[Clause]  = None

        pending_caption: str = ""

        # ── Helper: find or create a Clause container given the new hierarchy
        def _current_clause_container():
            """Return the tightest valid clause container."""
            if current_subsection:
                return current_subsection
            if current_section:
                return current_section      # fallback: direct on section
            return None

        # ── add_text: attach text to the current clause context ──────────────
        def add_text(text: str, page: int, has_inline_math: bool = False):
            nonlocal current_clause, current_section, current_subsection
            nonlocal current_part, current_division
            nonlocal current_pref_sec, current_pref_subsec
            nonlocal current_cf_sec

            if not text:
                return

            # ── Preface mode ──
            if mode == "preface":
                container = current_pref_subsec or current_pref_sec
                if container is None:
                    # Create a default preface section
                    self._preface_sec_counter += 1
                    ps = PrefaceSection(
                        id=f"PREF-SEC-{self._preface_sec_counter:02d}",
                        number="", title="Preface Content",
                        page_span=[page]
                    )
                    preface.sections.append(ps)
                    current_pref_sec = ps
                    container = ps
                _attach_text_to_content(container, text, page, has_inline_math)
                return

            # ── Conversion Factors mode ──
            if mode == "conversion_factors":
                if current_cf_sec is None:
                    self._cf_sec_counter += 1
                    current_cf_sec = ConversionFactorsSection(
                        id=f"CF-SEC-{self._cf_sec_counter:02d}",
                        number="", title="Conversion Factors Content",
                        page_span=[page]
                    )
                    conversion_factors.sections.append(current_cf_sec)
                _attach_text_to_content(current_cf_sec, text, page, has_inline_math)
                return

            # ── Normal / appendix mode ──
            if not current_clause:
                # Rescue orphaned text — create minimal structure
                if current_subsection:
                    current_clause = self._make_clause("", "Orphaned Content",
                                                       page, current_subsection)
                elif current_section:
                    current_clause = self._make_clause("", "Orphaned Content",
                                                       page, current_section)
                elif current_part:
                    # Create minimal section + subsection to hold orphan
                    current_section = self._make_section(
                        "0", "Preamble", page, current_part)
                    current_clause = self._make_clause("", "Orphaned Content",
                                                       page, current_section)
                else:
                    # No structure at all — route to preface if active
                    if preface.sections:
                        container = preface.sections[-1]
                        _attach_text_to_content(container, text, page, has_inline_math)
                    return

            _attach_text_to_content(current_clause, text, page, has_inline_math)

        def _attach_text_to_content(container, text: str, page: int,
                                    has_inline_math: bool = False):
            """Append text/sub_clause ContentItems to container.content."""
            if has_inline_math:
                markdown_text = inline_math_to_markdown(text)
                if markdown_text:
                    for line in markdown_text.splitlines():
                        sc = RE_SUBCLAUSE.match(line)
                        if sc:
                            container.content.append(ContentItem(
                                type="sub_clause",
                                marker=sc.group(1),
                                value=sc.group(2).strip(),
                            ))
                        elif line.strip():
                            container.content.append(ContentItem(
                                type="text", value=line.strip()
                            ))
            else:
                for line in text.splitlines():
                    m = RE_SUBCLAUSE.match(line)
                    if m:
                        container.content.append(ContentItem(
                            type="sub_clause",
                            marker=m.group(1),
                            value=m.group(2).strip(),
                        ))
                    elif line.strip():
                        container.content.append(ContentItem(
                            type="text", value=line.strip()
                        ))
            if hasattr(container, 'page_span') and page not in container.page_span:
                container.page_span.append(page)

        # ── Main block loop ───────────────────────────────────────────────────
        for block in blocks:
            btype = block["type"]
            text  = block.get("text", "")
            page  = block["page"]
            level = block.get("level", 0)

            # =================================================================
            # HEADINGS
            # =================================================================
            if btype == "heading":
                clean = re.sub(r'\s+', ' ', text).strip()

                has_hr = block.get("has_hr", False)

                # ── Priority 1: Division heading ──────────────────────────────
                m_div = RE_DIVISION.match(clean)
                if m_div:
                    div_letter = m_div.group(1).upper()
                    div_desc   = m_div.group(2).strip()  # empty for bare "Division X"
                    div_title  = div_desc or f"Division {div_letter}"
                    div_id     = f"DIV-{div_letter}"

                    # Rule 1: bare Division heading with <hr/> → actual content start
                    # Rule 2: descriptive heading in preface mode → preface reference
                    # Rule 3: everything else (TOC junk) → skip

                    if not div_desc and has_hr:
                        # Actual Division content marker (e.g., page 27 "Division A")
                        existing_div = next((d for d in divisions if d.id == div_id), None)
                        if existing_div:
                            current_division = existing_div
                            if div_title and len(div_title) > len(existing_div.title):
                                existing_div.title = div_title
                        else:
                            current_division = Division(
                                id=div_id, number=div_letter, title=div_title,
                                page_span=[page]
                            )
                            divisions.append(current_division)
                        mode               = "normal"
                        current_part       = None
                        current_section    = None
                        current_subsection = None
                        current_clause     = None
                        current_appendix   = None
                        current_notes_section = None
                        current_note_clause   = None

                    elif div_desc and (mode == "preface" or has_hr):
                        # Descriptive Division heading → Preface subsection reference
                        if mode == "preface":
                            if current_pref_sec is None:
                                self._preface_sec_counter += 1
                                self._preface_subsec_counter = 0
                                current_pref_sec = PrefaceSection(
                                    id=f"PREF-SEC-{self._preface_sec_counter:02d}",
                                    number="", title="Structure of the Code",
                                    page_span=[page]
                                )
                                preface.sections.append(current_pref_sec)
                            self._preface_subsec_counter += 1
                            pss = PrefaceSubsection(
                                id=f"PREF-SUBSEC-{self._preface_sec_counter:02d}-{self._preface_subsec_counter:02d}",
                                number="", title=clean, page_span=[page]
                            )
                            current_pref_sec.subsections.append(pss)
                            current_pref_subsec = pss
                    # else: TOC entry with no hr and not in preface → skip
                    continue

                # ── Priority 2: Preface heading ───────────────────────────────
                if RE_PREFACE.match(clean):
                    # Require <hr/> to distinguish actual preface content from TOC entries.
                    # The actual preface (page 11) has <hr/>; TOC entries (page 8) don't.
                    if has_hr:
                        mode = "preface"
                        if not preface.page_span:
                            preface.page_span = [page]
                        # Reset preface section context so new content goes into new sections
                        current_pref_sec    = None
                        current_pref_subsec = None
                    continue

                # ── Priority 3: Conversion Factors heading ────────────────────
                if RE_CONVERSION.match(clean):
                    # Require <hr/> for actual content; page 8/938 TOC entries lack it.
                    if has_hr:
                        mode = "conversion_factors"
                        if not conversion_factors.page_span:
                            conversion_factors.page_span = [page]
                        current_cf_sec = None
                    continue

                # ── Priority 4: Appendix heading (only in normal mode with division)
                if current_division:
                    m_app = RE_APPENDIX.match(clean)
                    if m_app:
                        app_letter = m_app.group(1).upper()
                        app_title  = m_app.group(2).strip() or f"Appendix {app_letter}"
                        app_id     = f"APP-{current_division.number}-{app_letter}"

                        existing_app = next(
                            (a for a in current_division.appendices if a.id == app_id), None)
                        if existing_app:
                            current_appendix = existing_app
                            if app_title and len(app_title) > len(existing_app.title):
                                existing_app.title = app_title
                        else:
                            current_appendix = Appendix(
                                id=app_id, number=app_letter, title=app_title,
                                page_span=[page]
                            )
                            current_division.appendices.append(current_appendix)

                        mode               = "appendix"
                        current_section    = None
                        current_subsection = None
                        current_clause     = None
                        current_notes_section = None
                        current_note_clause   = None
                        continue

                # =================================================================
                # Mode-specific heading handling
                # =================================================================

                # ── Priority 5: Notes to Part N heading ──────────────────────
                if has_hr and mode in ("normal", "init") and current_division:
                    m_notes = RE_NOTES_PART.match(clean)
                    if m_notes:
                        part_num = m_notes.group(1)
                        notes_title_suffix = m_notes.group(2).strip()
                        target_part = current_part
                        if target_part is None or target_part.number != part_num:
                            target_part = next(
                                (p for p in current_division.parts
                                 if p.number == part_num),
                                current_part
                            )
                        if target_part:
                            notes_sec_id = f"SEC-NOTES-{target_part.id}"
                            part_title_text = notes_title_suffix or target_part.title
                            notes_title = (
                                f"Notes to Part {part_num} {part_title_text}".strip()
                            )
                            existing_notes = self._notes_section_index.get(notes_sec_id)
                            if existing_notes is None:
                                existing_notes = Section(
                                    id=notes_sec_id, number="",
                                    title=notes_title, page_span=[page]
                                )
                                target_part.sections.append(existing_notes)
                                self._section_index[notes_sec_id] = existing_notes
                                self._notes_section_index[notes_sec_id] = existing_notes
                            else:
                                if page not in existing_notes.page_span:
                                    existing_notes.page_span.append(page)
                            current_notes_section = existing_notes
                            current_note_clause   = None
                            current_clause        = None
                            current_subsection    = None
                            current_section       = current_notes_section
                        continue

                # ── PREFACE mode ──────────────────────────────────────────────
                if mode == "preface":
                    # Use heading level to determine depth:
                    # h0/h2 → PrefaceSection; h3+ → PrefaceSubsection
                    if level in (0, 2) or (level == 1 and not RE_PART.match(clean)):
                        # New PrefaceSection
                        self._preface_sec_counter += 1
                        self._preface_subsec_counter = 0
                        ps = PrefaceSection(
                            id=f"PREF-SEC-{self._preface_sec_counter:02d}",
                            number="", title=clean, page_span=[page]
                        )
                        preface.sections.append(ps)
                        current_pref_sec    = ps
                        current_pref_subsec = None
                    else:
                        # PrefaceSubsection (h3, h4, h5)
                        if current_pref_sec is None:
                            # Create parent section if none exists
                            self._preface_sec_counter += 1
                            self._preface_subsec_counter = 0
                            current_pref_sec = PrefaceSection(
                                id=f"PREF-SEC-{self._preface_sec_counter:02d}",
                                number="", title="Preface", page_span=[page]
                            )
                            preface.sections.append(current_pref_sec)

                        self._preface_subsec_counter += 1
                        pss = PrefaceSubsection(
                            id=f"PREF-SUBSEC-{self._preface_sec_counter:02d}-{self._preface_subsec_counter:02d}",
                            number="", title=clean, page_span=[page]
                        )
                        current_pref_sec.subsections.append(pss)
                        current_pref_subsec = pss
                    continue

                # ── CONVERSION FACTORS mode ───────────────────────────────────
                if mode == "conversion_factors":
                    # h0 and h1 are document-level headings (title pages, volume markers).
                    # They signal content outside CF scope — reset context, don't create a section.
                    if level <= 1:
                        current_cf_sec = None
                        continue
                    self._cf_sec_counter += 1
                    current_cf_sec = ConversionFactorsSection(
                        id=f"CF-SEC-{self._cf_sec_counter:02d}",
                        number="", title=clean, page_span=[page]
                    )
                    conversion_factors.sections.append(current_cf_sec)
                    continue

                # ── NORMAL / APPENDIX / INIT mode ─────────────────────────────
                m_part = RE_PART.match(clean)
                m4     = RE_SENTENCE.match(clean)   # 4-part — check before m3
                m3     = RE_ARTICLE.match(clean)
                m2     = RE_SECTION.match(clean)

                if m_part:
                    # New Part under current division
                    part_num   = m_part.group(1)
                    part_title = m_part.group(2).strip() or clean
                    div_letter = current_division.number if current_division else "X"
                    part_id    = f"PART-{div_letter}-{part_num}"

                    parent_parts = current_division.parts if current_division else []
                    existing_part = next((p for p in parent_parts if p.id == part_id), None)
                    if existing_part:
                        current_part = existing_part
                        if part_title and len(part_title) > len(existing_part.title):
                            existing_part.title = part_title
                    else:
                        current_part = Part(
                            id=part_id, number=part_num, title=part_title,
                            page_span=[page]
                        )
                        if current_division:
                            current_division.parts.append(current_part)

                    mode               = "normal"
                    current_section    = None
                    current_subsection = None
                    current_clause     = None
                    current_appendix   = None
                    current_notes_section = None
                    current_note_clause   = None

                elif current_notes_section is not None:
                    # ── Notes mode: route all non-Part headings here ──────────
                    m_note_hdr = RE_NOTE_CLAUSE.match(clean)
                    if m_note_hdr:
                        note_num = m_note_hdr.group(1)
                        rest     = m_note_hdr.group(2).strip()
                        dot_m    = re.search(r'\.\s', rest)
                        if dot_m:
                            note_title = rest[:dot_m.start()].strip()
                        else:
                            note_title = rest.rstrip('.').strip()
                        current_note_clause = self._make_note_clause(
                            note_num, note_title, page, current_notes_section
                        )
                        current_clause = current_note_clause
                        if page not in current_notes_section.page_span:
                            current_notes_section.page_span.append(page)
                    else:
                        # Sub-heading within a note clause
                        if current_note_clause:
                            current_note_clause.content.append(
                                ContentItem(type="text", value=f"**{clean}**")
                            )
                            if page not in current_note_clause.page_span:
                                current_note_clause.page_span.append(page)

                elif m4 and (current_subsection or current_section):
                    # 4-number → Clause
                    num   = m4.group(1)
                    title = m4.group(2).lstrip(". ").strip() or num
                    container = current_subsection or self._ensure_subsection(
                        num, page, current_section)
                    if container:
                        current_clause = self._make_clause(num, title, page, container)

                elif m4 and current_part:
                    # 4-number but no section yet — create minimal parents
                    parts_list = num_to_parts(m4.group(1))
                    sec_num    = '.'.join(parts_list[:2])
                    sub_num    = '.'.join(parts_list[:3])
                    current_section    = self._make_section(sec_num, sec_num, page, current_part)
                    current_subsection = self._make_subsection(sub_num, sub_num, page, current_section)
                    num   = m4.group(1)
                    title = m4.group(2).lstrip(". ").strip() or num
                    current_clause = self._make_clause(num, title, page, current_subsection)

                elif m3 and (current_section or current_part or current_appendix):
                    # 3-number → Subsection
                    num   = m3.group(1)
                    title = m3.group(2).lstrip(". ").strip() or num
                    parent_sec = current_section
                    if parent_sec is None:
                        parent = current_appendix or current_part
                        if parent:
                            parent_sec = self._make_section(
                                '.'.join(num.split('.')[:2]), num, page, parent)
                    if parent_sec:
                        current_subsection = self._make_subsection(num, title, page, parent_sec)
                        current_clause = None

                elif m2 and (current_part or current_appendix):
                    # 2-number → Section
                    num   = m2.group(1)
                    title = m2.group(2).strip() or num
                    parent = current_appendix if mode == "appendix" else current_part
                    if parent:
                        current_section    = self._make_section(num, title, page, parent)
                        current_subsection = None
                        current_clause     = None

                elif m2 and current_section and not current_part:
                    # Mislabeled h1 — still a section
                    num, title = m2.group(1), (m2.group(2).strip() or m2.group(1))
                    current_section    = self._make_section(num, title, page, current_section)
                    current_subsection = None
                    current_clause     = None

                elif current_subsection:
                    # Plain label under a subsection → unnumbered Clause
                    current_clause = self._make_clause("", clean, page, current_subsection)

                elif current_section:
                    # Plain label under a section → unnumbered Clause
                    current_clause = self._make_clause("", clean, page, current_section)

                elif current_clause:
                    # Sub-label within current clause
                    current_clause.content.append(
                        ContentItem(type="text", value=f"**{clean}**"))
                    if page not in current_clause.page_span:
                        current_clause.page_span.append(page)
                # else: orphan heading before any structure — skip

            # =================================================================
            # TEXT
            # =================================================================
            elif btype == "text":
                has_inline_math = block.get("has_inline_math", False)
                first_line      = text.splitlines()[0] if text else ""
                check_line      = strip_html(first_line) if has_inline_math else first_line

                m4  = RE_SENTENCE.match(check_line)
                m3  = RE_ARTICLE.match(check_line)
                sec = RE_SECTION.match(check_line)

                if mode not in ("normal", "appendix", "init"):
                    add_text(text, page, has_inline_math)

                elif current_notes_section is not None:
                    # ── Notes mode text: detect new note clauses ──────────────
                    m_note = RE_NOTE_CLAUSE.match(check_line)
                    if m_note:
                        note_num      = m_note.group(1)
                        rest_of_line  = m_note.group(2).strip()
                        dot_m         = re.search(r'\.\s', rest_of_line)
                        if dot_m:
                            note_title       = rest_of_line[:dot_m.start()].strip()
                            first_line_tail  = rest_of_line[dot_m.end():]
                        else:
                            note_title      = rest_of_line.rstrip('.').strip()
                            first_line_tail = ""
                        current_note_clause = self._make_note_clause(
                            note_num, note_title, page, current_notes_section
                        )
                        current_clause = current_note_clause
                        if page not in current_notes_section.page_span:
                            current_notes_section.page_span.append(page)
                        # Attach remaining content from this block
                        remaining = text.splitlines()[1:] if len(text.splitlines()) > 1 else []
                        full_tail  = first_line_tail
                        if remaining:
                            full_tail = (full_tail + " " + " ".join(remaining)).strip()
                        if full_tail:
                            _attach_text_to_content(
                                current_note_clause, full_tail, page, has_inline_math
                            )
                    else:
                        # Continuation text → attach to current note clause
                        target = current_note_clause
                        if target is None:
                            target = self._make_note_clause(
                                "", "General Notes", page, current_notes_section
                            )
                            current_note_clause = target
                            current_clause      = target
                        _attach_text_to_content(
                            target, text, page, has_inline_math
                        )

                elif m4 and (current_subsection or current_section):
                    num = m4.group(1)
                    cid = f"CL-{num.replace('.', '-')}"
                    if cid not in self._clause_index:
                        title     = m4.group(2).lstrip(". ").strip() or num
                        container = current_subsection or self._ensure_subsection(
                            num, page, current_section)
                        if container:
                            current_clause = self._make_clause(num, title, page, container)
                    else:
                        add_text(text, page, has_inline_math)

                elif m3 and (current_section or current_part):
                    num = m3.group(1)
                    sid = f"SUBSEC-{num.replace('.', '-')}"
                    if sid not in self._subsec_index:
                        title      = m3.group(2).lstrip(". ").strip() or num
                        parent_sec = current_section
                        if parent_sec is None and current_part:
                            parent_sec = self._make_section(
                                '.'.join(num.split('.')[:2]), num, page, current_part)
                        if parent_sec:
                            current_subsection = self._make_subsection(
                                num, title, page, parent_sec)
                            current_clause = None
                    else:
                        add_text(text, page, has_inline_math)

                elif sec and current_part:
                    num   = sec.group(1)
                    sid   = f"SEC-{num.replace('.', '-')}"
                    if sid not in self._section_index:
                        title      = sec.group(2).strip()
                        current_section    = self._make_section(num, title, page, current_part)
                        current_subsection = None
                        current_clause     = None
                    else:
                        add_text(text, page, has_inline_math)

                else:
                    add_text(text, page, has_inline_math)

            # =================================================================
            # EQUATION
            # =================================================================
            elif btype == "equation":
                target = self._resolve_clause_target(
                    current_clause,
                    block.get("raw", {}).get("section_hierarchy", {}),
                    current_subsection, current_section
                )
                if target:
                    self._equation_counter += 1
                    eq_id  = f"EQ-{self._equation_counter}"
                    latex  = block.get("latex", text)
                    eq_obj = Equation(id=eq_id, latex=latex, page=page)
                    target.equations.append(eq_obj)
                    target.content.append(ContentItem(
                        type="equation", latex=latex, value=eq_id
                    ))
                    if page not in target.page_span:
                        target.page_span.append(page)

            # =================================================================
            # FIGURE
            # =================================================================
            elif btype == "figure":
                self._figure_counter += 1
                fig_id    = f"FIG-{self._figure_counter}"
                image_key = block.get("image_key", "")
                alt_text  = block.get("alt_text", "")
                caption   = block.get("caption", "")

                image_path = ""
                if image_key and image_key in self._images_dict:
                    image_path = save_image(
                        image_key,
                        self._images_dict[image_key],
                        self.figures_dir
                    )

                alt_stripped = alt_text.strip().lower()
                is_decorative = (
                    len(alt_stripped) < 60 and
                    any(kw == alt_stripped or alt_stripped.startswith(kw)
                        for kw in ("horizontal line", "vertical line", "divider",
                                   "separator", "solid black line", "decorative"))
                )
                if is_decorative:
                    self._figure_counter -= 1
                    continue

                fig_obj = Figure(
                    id=fig_id, caption=caption, alt_text=alt_text,
                    image_key=image_key, image_path=image_path, page=page
                )
                content_item = ContentItem(
                    type="figure", figure_id=fig_id,
                    image_key=image_key, image_path=image_path,
                    caption=caption, alt_text=alt_text
                )

                # Preface / ConversionFactors figure attachment
                if mode == "preface":
                    container = current_pref_subsec or current_pref_sec
                    if container:
                        container.figures.append(fig_obj)
                        container.content.append(content_item)
                        if page not in container.page_span:
                            container.page_span.append(page)
                    continue
                if mode == "conversion_factors":
                    if current_cf_sec:
                        current_cf_sec.figures.append(fig_obj)
                        current_cf_sec.content.append(content_item)
                        if page not in current_cf_sec.page_span:
                            current_cf_sec.page_span.append(page)
                    continue

                target = self._resolve_clause_target(
                    current_clause,
                    block.get("raw", {}).get("section_hierarchy", {}),
                    current_subsection, current_section
                )
                if target:
                    target.figures.append(fig_obj)
                    target.content.append(content_item)
                    if page not in target.page_span:
                        target.page_span.append(page)
                elif current_subsection or current_section:
                    # Orphan holder
                    container = current_subsection or current_section
                    orphan = self._make_clause(
                        "", caption or alt_text[:60] or f"Figure {fig_id}",
                        page, container
                    )
                    orphan.figures.append(fig_obj)
                    orphan.content.append(content_item)
                    current_clause = orphan

            # =================================================================
            # CAPTION (for tables)
            # =================================================================
            elif btype == "caption":
                pending_caption = text

            # =================================================================
            # TABLE
            # =================================================================
            elif btype == "table":
                # Preface / ConversionFactors table attachment
                if mode == "preface":
                    container = current_pref_subsec or current_pref_sec
                    if container:
                        self._table_counter += 1
                        tbl_id  = f"TBL-{self._table_counter}"
                        caption = pending_caption or f"Table {self._table_counter}"
                        pending_caption = ""
                        headers, rows = parse_table_html(text)
                        tbl_obj = Table(id=tbl_id, caption=caption,
                                        headers=headers, rows=rows, page=page)
                        container.tables.append(tbl_obj)
                        container.content.append(ContentItem(
                            type="table", table_id=tbl_id, value=caption))
                        if page not in container.page_span:
                            container.page_span.append(page)
                    else:
                        pending_caption = ""
                    continue

                if mode == "conversion_factors":
                    # Auto-create a CF section when a table arrives but no section exists yet
                    if current_cf_sec is None:
                        self._cf_sec_counter += 1
                        current_cf_sec = ConversionFactorsSection(
                            id=f"CF-SEC-{self._cf_sec_counter:02d}",
                            number="", title=pending_caption or "Conversion Factors",
                            page_span=[page]
                        )
                        conversion_factors.sections.append(current_cf_sec)
                    self._table_counter += 1
                    tbl_id  = f"TBL-{self._table_counter}"
                    caption = pending_caption or f"Table {self._table_counter}"
                    pending_caption = ""
                    headers, rows = parse_table_html(text)
                    tbl_obj = Table(id=tbl_id, caption=caption,
                                    headers=headers, rows=rows, page=page)
                    current_cf_sec.tables.append(tbl_obj)
                    current_cf_sec.content.append(ContentItem(
                        type="table", table_id=tbl_id, value=caption))
                    if page not in current_cf_sec.page_span:
                        current_cf_sec.page_span.append(page)
                    continue

                tbl_target = self._resolve_clause_target(
                    current_clause,
                    block.get("raw", {}).get("section_hierarchy", {}),
                    current_subsection, current_section
                )
                if tbl_target:
                    self._table_counter += 1
                    tbl_id  = f"TBL-{self._table_counter}"
                    caption = pending_caption or f"Table {self._table_counter}"
                    pending_caption = ""
                    headers, rows = parse_table_html(text)
                    tbl_obj = Table(
                        id=tbl_id, caption=caption,
                        headers=headers, rows=rows, page=page
                    )
                    tbl_target.tables.append(tbl_obj)
                    tbl_target.content.append(ContentItem(
                        type="table", table_id=tbl_id, value=caption
                    ))
                    if page not in tbl_target.page_span:
                        tbl_target.page_span.append(page)
                else:
                    pending_caption = ""

        # Post-processing
        self._remove_empty_clauses(preface, divisions)
        self._merge_continued_tables(divisions)
        # Remove CF sections that have no tables — conversion factor data is always tabular.
        # Sections with only text (from TOC pages or title pages captured in CF mode) are garbage.
        conversion_factors.sections = [
            s for s in conversion_factors.sections
            if s.tables
        ]
        return preface, divisions, conversion_factors

    # -------------------------------------------------------------------------
    # Hierarchy resolution helpers
    # -------------------------------------------------------------------------

    def _resolve_clause_target(self, current_clause, section_hierarchy: dict,
                                current_subsection, current_section) -> Optional[Clause]:
        """
        Return the best Clause to attach content to.
        1. current_clause if set
        2. Resolve via Datalab section_hierarchy dict
        3. Last clause in current_subsection or current_section
        """
        if current_clause:
            return current_clause

        if section_hierarchy and self._page_objects:
            resolved = self._resolve_hier_target(section_hierarchy)
            if resolved:
                return resolved

        if current_subsection and current_subsection.clauses:
            return current_subsection.clauses[-1]
        if current_section and current_section.clauses:
            return current_section.clauses[-1]
        # Check last subsection of current section
        if current_section and current_section.subsections:
            last_sub = current_section.subsections[-1]
            if last_sub.clauses:
                return last_sub.clauses[-1]
        return None

    def _resolve_hier_target(self, section_hierarchy: dict) -> Optional[Clause]:
        """
        Use Datalab section_hierarchy to find/create the owning Clause.
        Walks /page/{idx}/{type}/{child} paths via _page_objects.
        """
        for level_key in sorted(section_hierarchy, key=lambda k: -int(k)):
            ref_id = section_hierarchy[level_key]
            m = re.match(r'/page/(\d+)/\w+/(\d+)', ref_id)
            if not m:
                continue
            page_idx  = int(m.group(1))
            block_idx = int(m.group(2))
            if page_idx >= len(self._page_objects):
                continue
            children = self._page_objects[page_idx].get('children', [])
            if block_idx >= len(children):
                continue
            heading_text = strip_html(children[block_idx].get('html', '')).strip()
            if not heading_text:
                continue

            m4 = RE_SENTENCE.match(heading_text)
            m3 = RE_ARTICLE.match(heading_text)

            if m4:
                num = m4.group(1)
                cid = f"CL-{num.replace('.', '-')}"
                if cid in self._clause_index:
                    return self._clause_index[cid]
                # Not created yet — try to find parent subsection
                parts = num.split('.')
                if len(parts) >= 3:
                    sub_id = f"SUBSEC-{'-'.join(parts[:3])}"
                    if sub_id in self._subsec_index:
                        title = m4.group(2).lstrip('. ').strip() or num
                        return self._make_clause(num, title, page_idx + 1,
                                                  self._subsec_index[sub_id])
                    # Try parent section
                    sec_id = f"SEC-{'-'.join(parts[:2])}"
                    if sec_id in self._section_index:
                        sec = self._section_index[sec_id]
                        sub = self._make_subsection(
                            '.'.join(parts[:3]), '', page_idx + 1, sec)
                        title = m4.group(2).lstrip('. ').strip() or num
                        return self._make_clause(num, title, page_idx + 1, sub)
                continue

            if m3:
                sub_id = f"SUBSEC-{m3.group(1).replace('.', '-')}"
                if sub_id in self._subsec_index:
                    sub = self._subsec_index[sub_id]
                    if sub.clauses:
                        return sub.clauses[-1]
                # Fall through to section check
                sec_id = f"SEC-{m3.group(1).replace('.', '-').rsplit('-', 1)[0]}"
                if sec_id in self._section_index:
                    sec = self._section_index[sec_id]
                    if sec.subsections:
                        last_sub = sec.subsections[-1]
                        if last_sub.clauses:
                            return last_sub.clauses[-1]
                    if sec.clauses:
                        return sec.clauses[-1]
                continue

        return None

    def _ensure_subsection(self, clause_num: str, page: int,
                            section: Optional[Section]) -> Optional[object]:
        """
        Given a 4-part clause number, ensure its 3-part parent Subsection exists.
        Returns the Subsection (or section as fallback).
        """
        if not section:
            return None
        parts = clause_num.split('.')
        if len(parts) >= 3:
            sub_num = '.'.join(parts[:3])
            sub_id  = f"SUBSEC-{sub_num.replace('.', '-')}"
            if sub_id in self._subsec_index:
                return self._subsec_index[sub_id]
            # Auto-create subsection without a title (number-only)
            return self._make_subsection(sub_num, sub_num, page, section)
        return section   # fallback: direct on section

    # -------------------------------------------------------------------------
    # Object factory helpers
    # -------------------------------------------------------------------------

    def _make_section(self, number: str, title: str,
                      page: int, parent) -> Section:
        """
        Create (or reuse) a Section under parent (Part or Appendix).
        parent must have a .sections list.
        Non-numeric names get a parent-prefixed ID to avoid collisions.
        """
        if re.match(r'^\d', number):
            sid = f"SEC-{number.replace('.', '-')}"
        else:
            safe = re.sub(r'[^A-Za-z0-9]+', '-', number).strip('-')
            sid  = f"SEC-{getattr(parent, 'id', 'UNK')}-{safe}"

        existing = next((s for s in parent.sections if s.id == sid), None)
        if existing:
            if title and len(title) > len(existing.title):
                existing.title = title
            return existing

        sec = Section(id=sid, number=number, title=title, page_span=[page])
        parent.sections.append(sec)
        self._section_index[sid] = sec
        return sec

    def _make_subsection(self, number: str, title: str,
                         page: int, section: Section) -> Subsection:
        """Create (or reuse) a Subsection under a Section."""
        sid = f"SUBSEC-{number.replace('.', '-')}"
        existing = next((s for s in section.subsections if s.id == sid), None)
        if existing:
            if title and len(title) > len(existing.title):
                existing.title = title
            return existing

        sub = Subsection(id=sid, number=number, title=title, page_span=[page])
        section.subsections.append(sub)
        self._subsec_index[sid] = sub
        return sub

    def _make_clause(self, number: str, title: str,
                     page: int, parent) -> Clause:
        """
        Create a Clause under parent (Subsection or Section).
        parent must have a .clauses list.
        """
        cl = Clause(
            id=self._clause_id_for(number),
            number=number, title=title,
            page_span=[page]
        )
        parent.clauses.append(cl)
        self._clause_index[cl.id] = cl
        return cl

    def _clause_id_for(self, number: str) -> str:
        if number:
            return f"CL-{number.replace('.', '-')}"
        self._auto_clause_counter += 1
        return f"CL-AUTO-{self._auto_clause_counter}"

    def _note_clause_id_for(self, note_number: str) -> str:
        """Generate a stable ID for a note clause from its A-... number."""
        if not note_number:
            self._auto_clause_counter += 1
            return f"CL-NOTE-AUTO-{self._auto_clause_counter}"
        safe = note_number.replace('.', '-').replace('(', '-').replace(')', '-')
        return f"CL-NOTE-{safe}"

    def _make_note_clause(self, note_number: str, title: str,
                          page: int, notes_section: Section) -> Clause:
        """Create (or return existing) Clause for a note entry."""
        cl_id = self._note_clause_id_for(note_number)
        existing = self._clause_index.get(cl_id)
        if existing:
            if page not in existing.page_span:
                existing.page_span.append(page)
            return existing
        cl = Clause(id=cl_id, number=note_number, title=title,
                    page_span=[page])
        notes_section.clauses.append(cl)
        self._clause_index[cl_id] = cl
        return cl

    # -------------------------------------------------------------------------
    # Post-processing
    # -------------------------------------------------------------------------

    def _remove_empty_clauses(self, preface: Preface,
                               divisions: List[Division]):
        """Remove clauses that have no content, figures, tables, or equations."""
        def _clean_section(section: Section):
            for subsec in section.subsections:
                subsec.clauses = [
                    cl for cl in subsec.clauses
                    if cl.content or cl.figures or cl.tables or cl.equations
                ]
            section.clauses = [
                cl for cl in section.clauses
                if cl.content or cl.figures or cl.tables or cl.equations
            ]

        for div in divisions:
            for part in div.parts:
                for section in part.sections:
                    _clean_section(section)
            for appendix in div.appendices:
                for section in appendix.sections:
                    _clean_section(section)

    def _merge_continued_tables(self, divisions: List[Division]):
        """Merge multi-page (continued) table fragments within each clause."""
        cont_re = re.compile(r'\s*\(continued\)', re.IGNORECASE)

        def _tbl_number_norm(caption: str) -> str:
            cap = cont_re.sub('', caption).strip()
            m = re.match(r'(?:Table\s+)?([\d\.A-Za-z\-]+)', cap, re.IGNORECASE)
            if m:
                return re.sub(r'[.\-\s]', '', m.group(1)).lower()
            return cap.lower()

        def _process_clauses(clauses):
            for clause in clauses:
                if len(clause.tables) <= 1:
                    continue

                ids_to_remove: set = set()
                base_map: dict = {}

                for tbl in clause.tables:
                    cap     = tbl.caption
                    is_cont = bool(cont_re.search(cap))
                    norm    = _tbl_number_norm(cap)

                    if is_cont:
                        if norm in base_map:
                            base_map[norm].rows.extend(tbl.rows)
                            ids_to_remove.add(tbl.id)
                    else:
                        base_map[norm] = tbl

                if not ids_to_remove:
                    continue

                clause.tables = [t for t in clause.tables
                                 if t.id not in ids_to_remove]
                clause.content = [
                    item for item in clause.content
                    if not (item.type == "table" and item.table_id in ids_to_remove)
                ]

                # Cross-page rowspan carry (sandwich detection) for 2-col tables
                for tbl in clause.tables:
                    if len(tbl.headers) != 2:
                        continue
                    next_val: dict = {}
                    last = ""
                    for idx in range(len(tbl.rows) - 1, -1, -1):
                        v = tbl.rows[idx][1].strip() if len(tbl.rows[idx]) > 1 else ""
                        if v:
                            last = v
                        next_val[idx] = last

                    for idx, row in enumerate(tbl.rows):
                        if len(row) < 2:
                            continue
                        if row[1].strip() or not row[0].strip():
                            continue
                        prev = ""
                        for j in range(idx - 1, -1, -1):
                            pv = tbl.rows[j][1].strip() if len(tbl.rows[j]) > 1 else ""
                            if pv:
                                prev = pv
                                break
                        nxt = next_val.get(idx, "")
                        if prev and nxt and prev == nxt:
                            tbl.rows[idx][1] = prev

        def _process_section(section: Section):
            for subsec in section.subsections:
                _process_clauses(subsec.clauses)
            _process_clauses(section.clauses)

        for div in divisions:
            for part in div.parts:
                for section in part.sections:
                    _process_section(section)
            for appendix in div.appendices:
                for section in appendix.sections:
                    _process_section(section)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self, document: Document) -> dict:
        return asdict(document)


# =============================================================================
# Utility
# =============================================================================

def num_to_parts(number: str) -> List[str]:
    """Split a dot-notation number string into its parts list."""
    return number.split('.')


# =============================================================================
# Public entry point
# =============================================================================

def parse_datalab_output(datalab_result: dict, source_pdf: str = "unknown.pdf",
                         figures_dir: str = "storage/figures") -> dict:
    """
    Parse Datalab result → return JSON-serializable structured document dict.

    Top-level keys: title, source_pdf, total_pages, preface, divisions,
                    conversion_factors

    Called by main.py pipeline.
    """
    parser   = StructureParser(source_pdf=source_pdf, figures_dir=figures_dir)
    document = parser.parse(datalab_result)
    return parser.to_dict(document)
