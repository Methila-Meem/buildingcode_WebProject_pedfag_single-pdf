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
    clauses = []
    for ch in doc.get("chapters", []):
        for sec in ch.get("sections", []):
            for cl in sec.get("clauses", []):
                clauses.append(cl)
    return clauses


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
    chapters    = doc.get("chapters", [])
    stats       = doc.get("_stats", {})

    st.title("📊 Extraction Statistics")
    st.caption(f"Source: **{doc.get('title', 'Building Code')}** — `{doc.get('source_pdf', '')}`")
    st.divider()

    # ── Top-level counts ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages",    doc.get("total_pages", "?"))
    real_parts = sum(1 for ch in chapters if ch.get("number", "").isdigit())
    c2.metric("Parts",    real_parts)
    c3.metric("Sections", sum(len(ch.get("sections", [])) for ch in chapters))
    c4.metric("Clauses",  len(clause_list))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Equations", sum(len(cl.get("equations", [])) for cl in clause_list))
    c2.metric("Figures",   sum(len(cl.get("figures",   [])) for cl in clause_list))
    c3.metric("Tables",    sum(len(cl.get("tables",    [])) for cl in clause_list))
    c4.metric("🚩 Flagged", len(flags))

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
                "Clause":  cl.get("number"),
                "Ref Text": r.get("text"),
                "Kind":    r.get("kind"),
                "Target":  r.get("target_id", "—"),
            }
            for cl in clause_list
            for r in cl.get("references", [])
            if not r.get("resolved")
        ]
        if unresolved:
            st.markdown(f"**{len(unresolved)} unresolved** (external standards or appendices):")
            st.dataframe(pd.DataFrame(unresolved), use_container_width=True, hide_index=True)

    st.divider()

    # ── Per-Part breakdown ────────────────────────────────────────────────────
    st.subheader("Per-Part Breakdown")
    rows = []
    for ch in chapters:
        secs = ch.get("sections", [])
        cls  = [cl for s in secs for cl in s.get("clauses", [])]
        rows.append({
            "Part":      f"{ch['number']} — {ch['title']}",
            "Sections":  len(secs),
            "Clauses":   len(cls),
            "Equations": sum(len(cl.get("equations", [])) for cl in cls),
            "Figures":   sum(len(cl.get("figures",   [])) for cl in cls),
            "Tables":    sum(len(cl.get("tables",    [])) for cl in cls),
            "Flagged":   sum(1 for cl in cls if cl["id"] in flags),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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
