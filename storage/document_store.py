"""
storage/document_store.py
==========================
Handles saving and loading the structured document JSON.

We use a simple JSON file for the prototype.
This can be swapped for a database (PostgreSQL, SQLite) in later stages.
"""

import os
import json
from pathlib import Path

OUTPUT_DIR = Path("storage/output")


def save_document(document_dict: dict, filename: str = "structured_document.json") -> str:
    """
    Save the structured document dict to a JSON file.

    Args:
        document_dict: The fully structured and linked document
        filename:      Output filename (inside storage/output/)

    Returns:
        Full path to the saved file
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(document_dict, f, indent=2, ensure_ascii=False)

    size_kb = path.stat().st_size / 1024
    print(f"[Storage] Document saved to: {path}  ({size_kb:.1f} KB)")
    return str(path)


def load_document(filename: str = "structured_document.json") -> dict:
    """
    Load a previously saved structured document.

    Args:
        filename: JSON file inside storage/output/

    Returns:
        The document dict
    """
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found at {path}.\n"
            "Run main.py first to process a PDF."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _article_text_parts(article: dict) -> list:
    """
    Extract all searchable text parts from an article (and its nested sentences/clauses).
    Handles both new hierarchy (sentences[]) and notes/fallback content[].
    """
    parts = []

    # content[] items (notes mode / fallback)
    for item in article.get("content", []):
        itype = item.get("type", "")
        if itype in ("text", "sub_clause"):
            v = item.get("value", "").strip()
            if v:
                parts.append(v)
        elif itype == "equation":
            latex = item.get("latex", "").strip()
            if latex:
                parts.append(latex)
        elif itype == "figure":
            cap = item.get("caption", "").strip()
            alt = item.get("alt_text", "").strip()
            if cap:
                parts.append(cap)
            elif alt:
                parts.append(alt[:120])
        elif itype == "table":
            cap = item.get("value", "").strip()
            if cap:
                parts.append(cap)

    # sentences[] -> clauses[] -> subclauses[] (normal mode)
    for sent in article.get("sentences", []):
        if sent.get("content"):
            parts.append(sent["content"])
        for cl in sent.get("clauses", []):
            if cl.get("content"):
                parts.append(cl["content"])
            for sub in cl.get("subclauses", []):
                if sub.get("content"):
                    parts.append(sub["content"])

    # Tables and figures at article level
    for tbl in article.get("tables", []):
        cap = tbl.get("caption", "")
        if isinstance(cap, dict):
            cap = cap.get("raw", "")
        cap = cap.strip()
        if cap:
            parts.append(cap)
    for fig in article.get("figures", []):
        cap = fig.get("caption", "").strip()
        alt = fig.get("alt_text", "").strip()
        if cap:
            parts.append(cap)
        elif alt:
            parts.append(alt[:120])

    return parts


def _article_snippet(article: dict) -> str:
    """Extract a short snippet from an article for search result display."""
    # Try first sentence content
    for sent in article.get("sentences", []):
        if sent.get("content"):
            return sent["content"][:200]
    # Fall back to first content[] text item
    for item in article.get("content", []):
        if item.get("type") in ("text", "sub_clause"):
            v = item.get("value", "").strip()
            if v:
                return v[:200]
    return ""


def build_search_index(document_dict: dict) -> list:
    """
    Build a flat list of all searchable text entries from the document.
    Used by the FastAPI /search endpoint.

    Supports new hierarchy (divisions->parts->sections->subsections->articles)
    and old schema (chapters->sections->clauses) for backward compat.

    Returns:
        List of dicts: [{"id": "ART-4-1-2-1", "text": "...", "breadcrumb": "..."}, ...]
    """
    index = []

    # ── New schema: divisions -> parts -> sections -> subsections -> articles ──
    for div in document_dict.get("divisions", []):
        div_label = div.get("id", "")
        for part in div.get("parts", []):
            part_label = f"Part {part.get('number', '')}"
            for section in part.get("sections", []):
                sec_label = f"{part_label} > {section.get('number', '')}"
                for subsec in section.get("subsections", []):
                    sub_label = f"{sec_label} > {subsec.get('number', '')}"
                    for article in subsec.get("articles", subsec.get("clauses", [])):
                        art_label = f"{sub_label} > {article.get('number', '')}"
                        text_parts = _article_text_parts(article)
                        full_text = " ".join(text_parts)
                        snippet = _article_snippet(article)
                        index.append({
                            "id":         article["id"],
                            "type":       "article",
                            "number":     article.get("number", ""),
                            "title":      article.get("title", ""),
                            "text":       full_text,
                            "snippet":    snippet,
                            "breadcrumb": art_label,
                            "page":       (article.get("page_span") or [0])[0],
                        })
                for article in section.get("articles", section.get("clauses", [])):
                    art_label = f"{sec_label} > {article.get('number', '')}"
                    text_parts = _article_text_parts(article)
                    full_text = " ".join(text_parts)
                    snippet = _article_snippet(article)
                    index.append({
                        "id":         article["id"],
                        "type":       "article",
                        "number":     article.get("number", ""),
                        "title":      article.get("title", ""),
                        "text":       full_text,
                        "snippet":    snippet,
                        "breadcrumb": art_label,
                        "page":       (article.get("page_span") or [0])[0],
                    })

    # ── Old schema fallback: chapters -> sections -> clauses ──────────────────
    for chapter in document_dict.get("chapters", []):
        ch_label = f"Chapter {chapter.get('number', '')}"
        for section in chapter.get("sections", []):
            sec_label = f"{ch_label} > {section.get('number', '')}"
            for clause in section.get("clauses", []):
                cl_label = f"{sec_label} > {clause.get('number', '')}"
                content_parts = []
                for item in clause.get("content", []):
                    itype = item.get("type", "")
                    if itype in ("text", "sub_clause"):
                        v = item.get("value", "").strip()
                        if v:
                            content_parts.append(v)
                    elif itype == "equation":
                        latex = item.get("latex", "").strip()
                        if latex:
                            content_parts.append(latex)
                    elif itype == "figure":
                        cap = item.get("caption", "").strip()
                        alt = item.get("alt_text", "").strip()
                        if cap:
                            content_parts.append(cap)
                        elif alt:
                            content_parts.append(alt[:120])
                    elif itype == "table":
                        cap = item.get("value", "").strip()
                        if cap:
                            content_parts.append(cap)
                full_text = " ".join(content_parts)
                snippet = ""
                for item in clause.get("content", []):
                    if item.get("type") in ("text", "sub_clause"):
                        snippet = item.get("value", "").strip()
                        if snippet:
                            break
                index.append({
                    "id":         clause["id"],
                    "type":       "clause",
                    "number":     clause.get("number", ""),
                    "title":      clause.get("title", ""),
                    "text":       full_text,
                    "snippet":    snippet[:200],
                    "breadcrumb": cl_label,
                    "page":       clause.get("page_span", [0])[0],
                })

    return index