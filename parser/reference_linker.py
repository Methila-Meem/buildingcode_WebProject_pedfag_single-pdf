"""
parser/reference_linker.py
===========================
Scans every clause's content[] items for internal cross-references and
resolves them against the document ID index.

Two types of references handled:

1. Standard references (Sentence/Article/Section/Table/Figure):
   Sentence 4.1.6.5.(1)   -> CL-4-1-6-5
   Article 4.1.6.5.        -> CL-4-1-6-5
   Subsection 4.1.6.       -> SUBSEC-4-1-6  (always SUBSEC-; SEC- is fallback only)
   Section 4.1.            -> SEC-4-1
   Table 4.1.3.2.-A        -> TBL-N (caption lookup)
   Figure 4.1.6.5.-A       -> FIG-N (caption lookup)

2. Appendix note references (See Note A-...):
   (See Note A-4.1.3.2.(2).)  -> CL-AUTO-39  (if appendix is in this PDF)
   (See Note A-4.1.6.1.(1).)  -> None         (external - in a different PDF)

   Note references that resolve navigate to the appendix clause.
   Note references that don't resolve are still detected and displayed
   as styled badges so users know they exist.
"""

import re
from typing import Optional, List

# ─────────────────────────────────────────────────────────────────────────────
# Standard cross-reference patterns
# ─────────────────────────────────────────────────────────────────────────────
REFERENCE_PATTERNS = [
    re.compile(
        r'(?P<kind>Sentence|Article|Subsection|Section|Clause)\s+'
        r'(?P<ref>\d+(?:\.\d+)*(?:\.\d+)?(?:\([^)]+\))?)',
        re.IGNORECASE
    ),
    re.compile(
        r'(?P<kind>Table)\s+(?P<ref>[\d\.]+[\w\.\-]*)',
        re.IGNORECASE
    ),
    re.compile(
        r'(?P<kind>Figure)\s+(?P<ref>[\d\.]+[\w\.\-]*)',
        re.IGNORECASE
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Appendix note reference pattern
# Matches: "(See Note A-4.1.3.2.(2).)" and "See Note A-Table 4.1.2.1."
# Group 1 captures the full A- identifier including optional sentence number
# ─────────────────────────────────────────────────────────────────────────────
RE_NOTE = re.compile(
    r'See Note\s+(A-(?:Table\s+)?\d+(?:\.\d+)*(?:\.\(\d+\))?(?:\s+and\s+\(\d+\))*\.?)',
    re.IGNORECASE
)


# ─────────────────────────────────────────────────────────────────────────────
# Index builders
# ─────────────────────────────────────────────────────────────────────────────

def _iter_articles(document_dict: dict):
    """
    Yield every article dict from the new BCBC 2024 schema:
        divisions -> parts -> sections -> subsections -> articles
        divisions -> appendices -> sections -> subsections -> articles
    Also yields articles attached directly to sections (fallback).
    Also handles old schema with 'clauses' key for backward compat.
    """
    for div in document_dict.get("divisions", []):
        for part in div.get("parts", []):
            for section in part.get("sections", []):
                for subsec in section.get("subsections", []):
                    for article in subsec.get("articles", subsec.get("clauses", [])):
                        yield article
                for article in section.get("articles", section.get("clauses", [])):
                    yield article
        for appendix in div.get("appendices", []):
            for section in appendix.get("sections", []):
                for subsec in section.get("subsections", []):
                    for article in subsec.get("articles", subsec.get("clauses", [])):
                        yield article
                for article in section.get("articles", section.get("clauses", [])):
                    yield article


def _iter_clauses(document_dict: dict):
    """Backward compat alias for _iter_articles."""
    return _iter_articles(document_dict)


def build_id_index(document_dict: dict) -> dict:
    """
    Build flat {id -> node} lookup from the full document tree.
    Also builds caption-based lookups for Tables and Figures.
    Supports both old schema (chapters) and new schema (divisions).
    """
    index = {}

    # ── New schema: divisions -> parts -> sections -> subsections -> articles ──
    for div in document_dict.get("divisions", []):
        index[div["id"]] = div
        for part in div.get("parts", []):
            index[part["id"]] = part
            for section in part.get("sections", []):
                index[section["id"]] = section
                for subsec in section.get("subsections", []):
                    index[subsec["id"]] = subsec
                    for article in subsec.get("articles", subsec.get("clauses", [])):
                        index[article["id"]] = article
                        _index_clause_assets(article, index)
                        # Also index sentences, clauses, subclauses within article
                        for sent in article.get("sentences", []):
                            index[sent["id"]] = sent
                            for cl in sent.get("clauses", []):
                                index[cl["id"]] = cl
                                for sub in cl.get("subclauses", []):
                                    index[sub["id"]] = sub
                for article in section.get("articles", section.get("clauses", [])):
                    index[article["id"]] = article
                    _index_clause_assets(article, index)
                    for sent in article.get("sentences", []):
                        index[sent["id"]] = sent
                        for cl in sent.get("clauses", []):
                            index[cl["id"]] = cl
                            for sub in cl.get("subclauses", []):
                                index[sub["id"]] = sub
        for appendix in div.get("appendices", []):
            index[appendix["id"]] = appendix
            for section in appendix.get("sections", []):
                index[section["id"]] = section
                for subsec in section.get("subsections", []):
                    index[subsec["id"]] = subsec
                    for article in subsec.get("articles", subsec.get("clauses", [])):
                        index[article["id"]] = article
                        _index_clause_assets(article, index)
                        for sent in article.get("sentences", []):
                            index[sent["id"]] = sent
                            for cl in sent.get("clauses", []):
                                index[cl["id"]] = cl
                                for sub in cl.get("subclauses", []):
                                    index[sub["id"]] = sub
                for article in section.get("articles", section.get("clauses", [])):
                    index[article["id"]] = article
                    _index_clause_assets(article, index)
                    for sent in article.get("sentences", []):
                        index[sent["id"]] = sent
                        for cl in sent.get("clauses", []):
                            index[cl["id"]] = cl
                            for sub in cl.get("subclauses", []):
                                index[sub["id"]] = sub

    # ── Old schema fallback: chapters -> sections -> clauses ─────────────────
    for chapter in document_dict.get("chapters", []):
        index[chapter["id"]] = chapter
        for section in chapter.get("sections", []):
            index[section["id"]] = section
            for clause in section.get("clauses", []):
                index[clause["id"]] = clause
                _index_clause_assets(clause, index)

    return index


def _index_clause_assets(clause: dict, index: dict):
    """Register tables and figures from a clause into the id index."""
    for table in clause.get("tables", []):
        index[table["id"]] = table
        cap = table.get("caption", "")
        # Handle both legacy string captions and new structured dict captions
        if isinstance(cap, dict):
            raw = cap.get("raw", "")
            if raw:
                index[f"_cap_{raw}"] = table
            # Also index by canonical table_label for exact matching
            tbl_label = cap.get("table_label", "")
            if tbl_label and tbl_label != raw:
                index[f"_cap_{tbl_label}"] = table
        elif cap:
            index[f"_cap_{cap}"] = table
    for figure in clause.get("figures", []):
        index[figure["id"]] = figure
        # Use reference_key for canonical matching (set by _enrich_figures_in_dict)
        ref_key = figure.get("reference_key", "")
        if ref_key:
            index[f"_cap_{ref_key}"] = figure
        else:
            # Fallback: handle both flat string and structured dict captions
            cap = figure.get("caption", "")
            if isinstance(cap, dict):
                fig_label = cap.get("figure_label", "")
                cap_raw = cap.get("raw", "")
                for k in filter(None, {fig_label, cap_raw}):
                    index[f"_cap_{k}"] = figure
            elif cap:
                index[f"_cap_{cap}"] = figure


_RE_4PART_TITLE = re.compile(r'^(\d+\.\d+\.\d+\.\d+)')


def build_title_number_index(document_dict: dict) -> dict:
    """
    Build a secondary lookup: derived_cl_id -> actual_clause_id

    For every CL-AUTO-N clause whose title starts with a 4-part clause
    number (e.g. "1.1.1.1. Compliance with this Code"), we register the
    mapping CL-1-1-1-1 -> CL-AUTO-N.

    This covers clauses that were assigned CL-AUTO IDs by the parser
    because their heading came in at a level (h5) that the old handler
    always treated as unnumbered.  The reference linker generates target
    CL-1-1-1-1 from "Article 1.1.1.1" — without this index such
    references would always be unresolved even though the content exists.

    Only the first occurrence wins so that duplicate headings (e.g. the
    same Division-A clause appearing in both the cover chapter and the
    content chapter) consistently resolve to the first parse encounter.
    """
    title_num_index: dict = {}
    for article in _iter_articles(document_dict):
        # Skip articles that already have a proper number — they are
        # already reachable via their ART-X-X-X-X id in id_index.
        if article.get("number"):
            continue
        m = _RE_4PART_TITLE.match(article.get("title", ""))
        if m:
            # Register under both ART- and CL- prefixes for backward compat
            derived_art = "ART-" + m.group(1).replace(".", "-")
            derived_cl  = "CL-" + m.group(1).replace(".", "-")
            if derived_art not in title_num_index:
                title_num_index[derived_art] = article["id"]
            if derived_cl not in title_num_index:
                title_num_index[derived_cl] = article["id"]
    # Old schema fallback
    for chapter in document_dict.get("chapters", []):
        for section in chapter.get("sections", []):
            for clause in section.get("clauses", []):
                if clause.get("number"):
                    continue
                m = _RE_4PART_TITLE.match(clause.get("title", ""))
                if m:
                    derived_id = "CL-" + m.group(1).replace(".", "-")
                    if derived_id not in title_num_index:
                        title_num_index[derived_id] = clause["id"]
    return title_num_index


def build_note_index(document_dict: dict) -> dict:
    """
    Build a note reference -> [clause_id, ...] lookup.

    Scans all CL-AUTO-N clauses in two passes:

    Pass 1 — Clause title (existing behaviour):
        Clauses whose titles start with 'A-' are indexed by their A- identifier.
        e.g. 'A-4.1.3.2.(2) Load Combinations.' -> CL-AUTO-39

    Pass 2 — Embedded content text items (NEW):
        Many appendix notes are not separate clauses — they are sub-entries
        embedded as text blocks inside a larger CL-AUTO clause.  For example,
        CL-AUTO-40 (titled 'A-4.1.3.2.(4) ...') contains text items that begin
        with 'A-4.1.4.1.(2)', 'A-4.1.5.1.(1)', etc.  These were previously
        invisible to note resolution, leaving 62 note refs unresolved even
        though their content exists in the document.

        We now also scan the first line of every text content item in every
        CL-AUTO clause.  If the line begins with an A- identifier we register
        the containing clause as the navigation target for that note ref.

    Returns dict mapping note key -> list of matching clause IDs (deduplicated,
    ordered by first occurrence).
    e.g. {'A-4.1.3.2': ['CL-AUTO-39', 'CL-AUTO-40'],
          'A-4.1.4.1': ['CL-AUTO-40'], ...}
    """
    RE_A_TITLE = re.compile(
        r'(A-(?:Table\s+)?\d+(?:\.\d+)*(?:\.\(\d+\))?(?:\s+and\s+\(\d+\))?)',
    )
    note_idx = {}

    def _process_article_for_notes(article):
        cid = article.get("id", "")
        # Handle both new (ART-NOTE/ART-AUTO) and old (CL-NOTE/CL-AUTO) prefixes
        is_note_article = (cid.startswith("ART-NOTE") or cid.startswith("CL-NOTE"))
        is_auto_article = (cid.startswith("ART-AUTO") or cid.startswith("CL-AUTO"))
        if not (is_auto_article or is_note_article):
            return
        title = article.get("title", "")
        # Pass 1: index the article title
        if title.startswith("A-") or is_note_article:
            m = RE_A_TITLE.match(title) if title.startswith("A-") else None
            # For ART-NOTE/CL-NOTE articles, use the number field directly
            if m is None and is_note_article:
                num = article.get("number", "")
                if num.startswith("A-"):
                    m_num = RE_A_TITLE.match(num)
                    if m_num:
                        key = m_num.group(1).strip().rstrip('.')
                        base = re.sub(r'\.\(\d+\).*$', '', key)
                        for k in {key, base}:
                            if cid not in note_idx.get(k, []):
                                note_idx.setdefault(k, []).append(cid)
            elif m:
                key = m.group(1).strip().rstrip('.')
                if cid not in note_idx.get(key, []):
                    note_idx.setdefault(key, []).append(cid)
        # Pass 2: index embedded A- sub-entries in content text
        for item in article.get("content", []):
            if item.get("type") not in ("text", "sub_clause"):
                continue
            val = item.get("value", "").strip()
            if not val.startswith("A-"):
                continue
            m = RE_A_TITLE.match(val)
            if not m:
                continue
            full_key = m.group(1).strip().rstrip('.')
            base_key = re.sub(r'\.\(\d+\).*$', '', full_key)
            for key in {full_key, base_key}:
                if cid not in note_idx.get(key, []):
                    note_idx.setdefault(key, []).append(cid)

    # Walk new schema
    for article in _iter_articles(document_dict):
        _process_article_for_notes(article)
    # Old schema fallback
    for chapter in document_dict.get("chapters", []):
        for section in chapter.get("sections", []):
            for clause in section.get("clauses", []):
                _process_article_for_notes(clause)

    return note_idx


# ─────────────────────────────────────────────────────────────────────────────
# Reference resolution helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_ref(s: str) -> str:
    """
    Normalize a Figure/Table identifier for caption lookup.

    Strips trailing dots and removes all dots and hyphens from the numeric
    portion so that typos in source captions (e.g. "4.1.76.-C" instead of
    "4.1.7.6.-C") and trailing-dot variants ("4.1.6.5.-A.") both map to
    the same comparison key.

    Examples::

        "4.1.6.5.-A."  -> "4165a"
        "4.1.6.5.-A"   -> "4165a"
        "4.1.76.-C"    -> "4176c"   (typo in source)
        "4.1.7.6.-C"   -> "4176c"   (reference text)
    """
    return re.sub(r'[.\-]', '', s.rstrip('.')).lower()


def _ref_to_id(ref: str, kind: str, id_index: dict,
               title_num_index: Optional[dict] = None) -> Optional[str]:
    """
    Convert a standard reference string to a document node ID.

    Fix 1 — CL-AUTO fallback via title_num_index:
      For Sentence/Article/Clause references, if the derived CL-X-X-X-X id is
      not in id_index, check title_num_index (maps derived id -> actual CL-AUTO
      id for clauses whose number is only in their title).

    Fix 5 — SEC→CL fallback:
      For Subsection/Section references, if the derived SEC-X-X-X id is not in
      id_index, try a CL-X-X-X fallback (handles cases where the parser created
      a Clause rather than a Section for 3-part numbered headings).

    Also:
      - Strip trailing dots from Figure/Table refs before caption lookup.
      - Use normalized comparison (dots/hyphens stripped) for fuzzy caption
        matching so source-PDF typos resolve correctly.

    Subsection always maps to SUBSEC- regardless of the number of dot-parts.
    "4.1.4" has 3 parts but is still a Subsection (SUBSEC-4-1-4), not a Clause.
    SEC- is a fallback only when no SUBSEC- node exists in the id_index.
    """
    kind_lower = kind.lower()
    # Normalize: strip trailing dot before building the fallback ID
    ref_clean  = ref.rstrip('.')
    normalized = re.sub(r'[.\-]', '-', ref_clean).strip('-')

    if kind_lower in ("sentence", "article", "clause"):
        # Try new ART- prefix first, then fall back to CL- for old docs
        art_target = f"ART-{normalized}"
        if art_target in id_index:
            return art_target
        target = f"CL-{normalized}"
        # Fix 1: if not found directly, look up via title-number index
        if target not in id_index and title_num_index:
            actual = title_num_index.get(art_target) or title_num_index.get(target)
            if actual:
                return actual
        # Return ART- target if neither found (new schema default)
        if art_target not in id_index and target not in id_index:
            return art_target
        return target if target in id_index else art_target

    if kind_lower == "subsection":
        # Subsection always maps to SUBSEC-* (never SEC-*)
        target = f"SUBSEC-{normalized}"
        if target in id_index:
            return target
        # Fallbacks: some 3-part headings may have been parsed as Section, Article, or Clause
        sec_target = f"SEC-{normalized}"
        if sec_target in id_index:
            return sec_target
        art_target = f"ART-{normalized}"
        if art_target in id_index:
            return art_target
        cl_target = f"CL-{normalized}"
        if cl_target in id_index:
            return cl_target
        return target  # return SUBSEC- even if not found (consistent prefix)

    if kind_lower == "section":
        target = f"SEC-{normalized}"
        # Fix 5: if SEC- not found, try matching as an Article (ART-) or Clause (CL-)
        if target not in id_index:
            art_target = f"ART-{normalized}"
            if art_target in id_index:
                return art_target
            cl_target = f"CL-{normalized}"
            if cl_target in id_index:
                return cl_target
        return target

    if kind_lower == "table":
        ref_norm = _normalize_ref(ref_clean)
        for key, node in id_index.items():
            if not key.startswith("_cap_"):
                continue
            # Only match table nodes (TBL- prefix) to avoid collision with figure caps
            if not node.get("id", "").startswith("TBL-"):
                continue
            cap_body = key[len("_cap_"):]
            cap_m    = re.match(r'(?:Table\s+)?([\d\.]+[\w\.\-]*)', cap_body, re.IGNORECASE)
            if cap_m and _normalize_ref(cap_m.group(1)) == ref_norm:
                return node.get("id", "")
        return f"TBL-{normalized}"

    if kind_lower == "figure":
        ref_norm = _normalize_ref(ref_clean)
        # Try exact canonical key first: reference_key = "Figure {number}"
        exact_cap_key = f"_cap_Figure {ref_clean}"
        if exact_cap_key in id_index:
            node = id_index[exact_cap_key]
            if node.get("id", "").startswith("FIG-"):
                return node["id"]
        # Fuzzy fallback: only match FIG- nodes to avoid collision with table caps
        for key, node in id_index.items():
            if not key.startswith("_cap_"):
                continue
            if not node.get("id", "").startswith("FIG-"):
                continue
            cap_body = key[len("_cap_"):]
            cap_m    = re.match(r'(?:Figure\s+)?([\d\.]+[\w\.\-]*)', cap_body, re.IGNORECASE)
            if cap_m and _normalize_ref(cap_m.group(1)) == ref_norm:
                return node.get("id", "")
        return f"FIG-{normalized}"

    return None


def _resolve_note(note_ref: str, note_index: dict) -> List[str]:
    """
    Resolve a note reference string to a list of clause IDs.

    Tries exact match first, then base match (without sentence number).

    e.g. "A-4.1.3.2.(2)" -> tries "A-4.1.3.2.(2)" then "A-4.1.3.2"
         "A-4.1.7.5."    -> tries "A-4.1.7.5." then "A-4.1.7.5"

    Returns [] if the note is not in this PDF (external reference).
    """
    clean = note_ref.strip().rstrip('.')

    # Exact match
    if clean in note_index:
        return note_index[clean]

    # Match without sentence number: "A-4.1.3.2.(2)" -> "A-4.1.3.2"
    base = re.sub(r'\.\(\d+\).*$', '', clean)
    if base in note_index:
        return note_index[base]

    return []


def _extract_refs_from_text(text: str) -> list:
    """Scan a text string for all standard reference patterns."""
    found = []
    seen  = set()
    for pattern in REFERENCE_PATTERNS:
        for m in pattern.finditer(text):
            raw  = m.group(0)
            ref  = m.group("ref")
            kind = m.group("kind")
            key  = (kind.lower(), ref)
            if key not in seen:
                seen.add(key)
                found.append({"raw": raw, "ref": ref, "kind": kind})
    return found


def _extract_notes_from_text(text: str) -> list:
    """
    Scan a text string for all (See Note A-...) references.

    Returns list of dicts:
        [{"raw": "(See Note A-4.1.3.2.(2).)", "note_ref": "A-4.1.3.2.(2)."}, ...]
    """
    found = []
    seen  = set()
    for m in RE_NOTE.finditer(text):
        note_ref = m.group(1).strip()
        if note_ref not in seen:
            seen.add(note_ref)
            found.append({
                "raw":      m.group(0),
                "note_ref": note_ref,
            })
    return found


# ─────────────────────────────────────────────────────────────────────────────
# Table reference resolution
# ─────────────────────────────────────────────────────────────────────────────

_RE_SENT_NUM = re.compile(r'^(\d+\.\d+\.\d+\.\d+)\s*[.\s]*\((\d+)\)')


def _link_table_references(document_dict: dict, id_index: dict,
                            title_num_index: dict) -> None:
    """
    Walk all tables in the document dict and resolve the target_id / resolved
    fields on references that were extracted during table enrichment.

    Handles:
    - caption.forming_part_of reference
    - each cell's references[]
    - the table-level references[] (deduped, so resolving cells is sufficient)

    For Sentence references, tries the SENT- ID format first before falling
    back to the standard _ref_to_id() logic.
    """
    def _resolve_one(ref_dict: dict) -> None:
        if ref_dict.get("resolved"):
            return
        kind   = ref_dict.get("kind", "")
        number = ref_dict.get("number", "")
        if not kind or not number:
            return

        # For Sentence references try SENT-X-Y-Z-W-N first
        if kind.lower() == "sentence":
            m = _RE_SENT_NUM.match(number)
            if m:
                art_safe = m.group(1).replace('.', '-')
                n        = m.group(2)
                sent_id  = f"SENT-{art_safe}-{n}"
                if sent_id in id_index:
                    ref_dict["target_id"] = sent_id
                    ref_dict["resolved"]  = True
                    return

        target_id = _ref_to_id(number, kind, id_index, title_num_index)
        if target_id:
            is_resolved = target_id in id_index
            ref_dict["target_id"] = target_id
            ref_dict["resolved"]  = is_resolved

    def _process_table(tbl: dict) -> None:
        # Resolve caption.forming_part_of
        cap = tbl.get("caption", {})
        if isinstance(cap, dict) and cap.get("forming_part_of"):
            _resolve_one(cap["forming_part_of"])

        # Resolve cell references (rows are structured dicts)
        for row in tbl.get("rows", []):
            if not isinstance(row, dict):
                continue
            for cell in row.get("cells", []):
                for ref in cell.get("references", []):
                    _resolve_one(ref)

        # Resolve table-level references (re-resolve so they match cells)
        for ref in tbl.get("references", []):
            _resolve_one(ref)

    def _walk(node) -> None:
        if isinstance(node, dict):
            for tbl in node.get("tables", []):
                _process_table(tbl)
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(document_dict)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def link_references(document_dict: dict) -> dict:
    """
    Walk all clauses, detect both standard references and note references,
    resolve each, and attach to clause.references[] and clause.note_refs[].

    Standard refs -> clause.references[]
      [{"text": "Article 4.1.6.5.", "kind": "Article",
        "target_id": "CL-4-1-6-5", "resolved": True}, ...]

    Note refs -> clause.note_refs[]
      [{"raw": "(See Note A-4.1.3.2.(2).)", "note_ref": "A-4.1.3.2.(2).",
        "target_ids": ["CL-AUTO-39", "CL-AUTO-40"], "resolved": True}, ...]

    Items in clause.note_refs[]:
      resolved=True  -> target_ids contains one or more CL-AUTO IDs (clickable)
      resolved=False -> external appendix note (styled badge, not clickable)
    """
    id_index        = build_id_index(document_dict)
    note_index      = build_note_index(document_dict)
    title_num_index = build_title_number_index(document_dict)

    total_refs    = resolved_refs    = 0
    total_notes   = resolved_notes   = 0

    # Walk new schema (divisions) + old schema fallback (chapters)
    all_articles = list(_iter_articles(document_dict))
    for chapter in document_dict.get("chapters", []):
        for section in chapter.get("sections", []):
            all_articles.extend(section.get("clauses", []))

    for clause in all_articles:
        texts = [clause.get("title", "")]
        # Content items (notes/fallback)
        for item in clause.get("content", []):
            if item.get("type") in ("text", "sub_clause"):
                texts.append(item.get("value", ""))
        # Sentences and their nested clauses/subclauses
        for sent in clause.get("sentences", []):
            if sent.get("content"):
                texts.append(sent["content"])
            for cl in sent.get("clauses", []):
                if cl.get("content"):
                    texts.append(cl["content"])
                for sub in cl.get("subclauses", []):
                    if sub.get("content"):
                        texts.append(sub["content"])

        # ── Standard references ───────────────────────────────────────────
        linked    = []
        seen_refs = set()
        for text in texts:
            for det in _extract_refs_from_text(text):
                key = (det["kind"].lower(), det["ref"])
                if key in seen_refs:
                    continue
                seen_refs.add(key)
                total_refs += 1
                target_id   = _ref_to_id(det["ref"], det["kind"], id_index, title_num_index)
                is_resolved = bool(target_id and target_id in id_index)
                if is_resolved:
                    resolved_refs += 1
                ref_entry = {
                    "text":      det["raw"],
                    "kind":      det["kind"],
                    "number":    det["ref"],
                    "target_id": target_id,
                    "resolved":  is_resolved,
                }
                # Add lookup_key for Figure references (canonical matching key)
                if det["kind"].lower() == "figure":
                    ref_entry["lookup_key"] = f"Figure {det['ref']}"
                linked.append(ref_entry)
        clause["references"] = linked

        # ── Note references ───────────────────────────────────────────────
        note_linked = []
        seen_notes  = set()
        for text in texts:
            for det in _extract_notes_from_text(text):
                nr = det["note_ref"]
                if nr in seen_notes:
                    continue
                seen_notes.add(nr)
                total_notes += 1
                target_ids  = _resolve_note(nr, note_index)
                is_resolved = len(target_ids) > 0
                if is_resolved:
                    resolved_notes += 1
                note_linked.append({
                    "raw":        det["raw"],
                    "note_ref":   nr,
                    "target_ids": target_ids,
                    "resolved":   is_resolved,
                })
        clause["note_refs"] = note_linked

    # Resolve target IDs for table caption and cell references
    _link_table_references(document_dict, id_index, title_num_index)

    ref_rate  = round(resolved_refs  / total_refs  * 100, 1) if total_refs  else 0.0
    note_rate = round(resolved_notes / total_notes * 100, 1) if total_notes else 0.0

    print(f"[References] {resolved_refs}/{total_refs} resolved ({ref_rate}%)")
    print(f"[Note refs]  {resolved_notes}/{total_notes} resolved ({note_rate}%) "
          f"— unresolved are external appendix notes in other PDFs")

    document_dict["_stats"] = {
        "total_references":        total_refs,
        "resolved_references":     resolved_refs,
        "resolution_rate_pct":     ref_rate,
        "total_note_refs":         total_notes,
        "resolved_note_refs":      resolved_notes,
        "note_resolution_rate_pct": note_rate,
    }
    return document_dict