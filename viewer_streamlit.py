"""
viewer_streamlit.py
====================
Streamlit viewer — Extraction Statistics for structured building code documents.

Run with:
    streamlit run viewer_streamlit.py
"""

import json
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Building Code — Extraction Statistics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
STRUCTURED_DOC_PATH = Path("storage/output/structured_document.json")
FLAGS_PATH          = Path("storage/output/flagged_issues.json")


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_document():
    if not STRUCTURED_DOC_PATH.exists():
        return None
    with open(STRUCTURED_DOC_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_flags() -> dict:
    if not FLAGS_PATH.exists():
        return {}
    with open(FLAGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_clause_list(doc: dict) -> list:
    """
    Collect all articles (formerly clauses) from the new schema:
        divisions -> parts -> sections -> subsections -> articles
    Also collects articles attached directly to sections (fallback).
    Includes appendices under each division.
    Handles both new 'articles' key and old 'clauses' key for backward compat.
    """
    articles = []
    for div in doc.get("divisions", []):
        for part in div.get("parts", []):
            for sec in part.get("sections", []):
                for sub in sec.get("subsections", []):
                    articles.extend(sub.get("articles", sub.get("clauses", [])))
                articles.extend(sec.get("articles", sec.get("clauses", [])))
        for appendix in div.get("appendices", []):
            for sec in appendix.get("sections", []):
                for sub in sec.get("subsections", []):
                    articles.extend(sub.get("articles", sub.get("clauses", [])))
                articles.extend(sec.get("articles", sec.get("clauses", [])))
    return articles


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    doc = load_document()

    if doc is None:
        st.title("Building Code — Extraction Statistics")
        st.error("No structured document found.")
        st.info(
            "Run:  `python main.py your_building_code.pdf`\n\n"
            f"Expected: `{STRUCTURED_DOC_PATH}`"
        )
        return

    flags       = load_flags()
    clause_list = build_clause_list(doc)
    divisions   = doc.get("divisions", [])
    stats       = doc.get("_stats", {})

    # Aggregate counts
    total_parts    = sum(len(dv.get("parts", [])) for dv in divisions)
    total_sections = sum(
        len(p.get("sections", []))
        for dv in divisions for p in dv.get("parts", [])
    )
    total_subsecs  = sum(
        len(s.get("subsections", []))
        for dv in divisions for p in dv.get("parts", [])
        for s in p.get("sections", [])
    )

    st.title("📊 Extraction Statistics")
    st.caption(f"Source: **{doc.get('title', 'Building Code')}** — `{doc.get('source_pdf', '')}`")
    st.divider()

    # ── Top-level counts ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages",       doc.get("total_pages", "?"))
    c2.metric("Parts",       total_parts)
    c3.metric("Sections",    total_sections)
    c4.metric("Subsections", total_subsecs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Articles",  len(clause_list))
    c2.metric("Equations", sum(len(art.get("equations", [])) for art in clause_list))
    c3.metric("Figures",   sum(len(art.get("figures",   [])) for art in clause_list))
    c4.metric("Tables",    sum(len(art.get("tables",    [])) for art in clause_list))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚩 Flagged", len(flags))
    c2.metric("Divisions",  len(divisions))
    cf_tables = sum(
        len(s.get("tables", []))
        for s in doc.get("conversion_factors", {}).get("sections", [])
    )
    c3.metric("CF Tables",  cf_tables)
    pref_secs = len(doc.get("preface", {}).get("sections", []))
    c4.metric("Preface Sections", pref_secs)

    st.divider()

    # ── Reference resolution ──────────────────────────────────────────────────
    if stats:
        st.subheader("Reference Resolution")
        total    = stats.get("total_references", 0)
        resolved = stats.get("resolved_references", 0)
        rate     = stats.get("resolution_rate_pct", 0)
        c1, c2, c3 = st.columns(3)
        c1.metric("Found",    total)
        c2.metric("Resolved", resolved)
        c3.metric("Rate",     f"{rate}%")
        st.progress(int(rate) / 100)

        total_notes    = stats.get("total_note_refs", 0)
        resolved_notes = stats.get("resolved_note_refs", 0)
        note_rate      = stats.get("note_resolution_rate_pct", 0)
        if total_notes > 0:
            st.markdown(
                f"**Appendix note refs:** {resolved_notes}/{total_notes} "
                f"in this PDF ({note_rate}%) — "
                f"{total_notes - resolved_notes} are external (in other PDFs)"
            )

        unresolved = [
            {
                "Article":  art.get("number"),
                "Ref Text": r.get("text"),
                "Kind":     r.get("kind"),
                "Target":   r.get("target_id", "—"),
            }
            for art in clause_list
            for r in art.get("references", [])
            if not r.get("resolved")
        ]
        if unresolved:
            st.markdown(f"**{len(unresolved)} unresolved** (external standards or appendices):")
            st.dataframe(pd.DataFrame(unresolved), use_container_width=True, hide_index=True)

    st.divider()

    # ── Per-Division / Per-Part breakdown ─────────────────────────────────────
    st.subheader("Per-Division Breakdown")
    div_rows = []
    for dv in divisions:
        parts = dv.get("parts", [])
        all_secs  = [s for p in parts for s in p.get("sections", [])]
        all_subs  = [sub for s in all_secs for sub in s.get("subsections", [])]
        all_arts  = (
            [art for sub in all_subs for art in sub.get("articles", sub.get("clauses", []))] +
            [art for s in all_secs for art in s.get("articles", s.get("clauses", []))]
        )
        appendices = dv.get("appendices", [])
        div_rows.append({
            "Division":    f"{dv['id']} — {dv.get('title', '')}",
            "Parts":       len(parts),
            "Sections":    len(all_secs),
            "Subsections": len(all_subs),
            "Articles":    len(all_arts),
            "Equations":   sum(len(art.get("equations", [])) for art in all_arts),
            "Figures":     sum(len(art.get("figures",   [])) for art in all_arts),
            "Tables":      sum(len(art.get("tables",    [])) for art in all_arts),
            "Appendices":  len(appendices),
            "Flagged":     sum(1 for art in all_arts if art["id"] in flags),
        })
    st.dataframe(pd.DataFrame(div_rows), use_container_width=True, hide_index=True)

    st.subheader("Per-Part Breakdown")
    part_rows = []
    for dv in divisions:
        for part in dv.get("parts", []):
            secs  = part.get("sections", [])
            subs  = [sub for s in secs for sub in s.get("subsections", [])]
            arts  = (
                [art for sub in subs for art in sub.get("articles", sub.get("clauses", []))] +
                [art for s in secs for art in s.get("articles", s.get("clauses", []))]
            )
            part_rows.append({
                "Division":    dv["id"],
                "Part":        f"Part {part['number']} — {part.get('title', '')}",
                "Sections":    len(secs),
                "Subsections": len(subs),
                "Articles":    len(arts),
                "Equations":   sum(len(art.get("equations", [])) for art in arts),
                "Figures":     sum(len(art.get("figures",   [])) for art in arts),
                "Tables":      sum(len(art.get("tables",    [])) for art in arts),
                "Flagged":     sum(1 for art in arts if art["id"] in flags),
            })
    st.dataframe(pd.DataFrame(part_rows), use_container_width=True, hide_index=True)

    st.divider()

    # ── Downloads ─────────────────────────────────────────────────────────────
    st.subheader("Downloads")
    st.download_button(
        "⬇ Download structured_document.json",
        data=json.dumps(doc, indent=2),
        file_name="structured_document.json",
        mime="application/json",
    )

    raw_path = Path("storage") / f"raw_{Path(doc.get('source_pdf', '')).stem}.json"
    if raw_path.exists():
        raw_text = raw_path.read_text(encoding="utf-8")
        st.download_button(
            f"⬇ Download {raw_path.name}",
            data=raw_text,
            file_name=raw_path.name,
            mime="application/json",
        )
        with st.expander("Preview raw JSON (first 200 lines)"):
            lines = raw_text.splitlines()
            st.code(
                "\n".join(lines[:200]) + ("\n..." if len(lines) > 200 else ""),
                language="json",
            )
    else:
        st.info(f"Raw cache not found at `{raw_path}`.")


if __name__ == "__main__":
    main()
