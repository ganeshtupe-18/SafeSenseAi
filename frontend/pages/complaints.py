"""
frontend/pages/complaints.py
─────────────────────────────────────────────────────────
Phase 3 – Food Complaint System + NLP  (Akash's module)

Standalone : streamlit run frontend/pages/complaints.py
Integrated : from frontend.pages.complaints import show; show()

Shared theme used:
  shared/theme/colors.py     → COLORS palette
  shared/theme/styles.py     → apply_global_styles()
  shared/theme/components.py → section_title(), status_badge()
  shared/constants.py        → COMPLAINT_STATUSES
─────────────────────────────────────────────────────────
"""

from __future__ import annotations

# ── sys.path fix so module imports resolve when run standalone ────────────────
import sys
import os as _os

_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
from datetime import date

# ── Shared theme  (read-only — do NOT modify these files) ────────────────────
from shared.theme.styles import apply_global_styles
from shared.theme.colors import COLORS
from shared.theme.components import section_title  # status_badge available if needed

# ── Shared constants ──────────────────────────────────────────────────────────
from shared.constants import COMPLAINT_STATUSES

# ── Complaint module imports ──────────────────────────────────────────────────
from modules.complaints.service import (
    CATEGORIES,
    get_all_complaints,
    get_complaint_by_id,
    submit_complaint,
    update_complaint_status,
    get_stats,
)
from modules.complaints.ml.classifier import predict_category
from modules.complaints.ml.duplicate_detection import find_duplicates

# ── Standalone page config guard ─────────────────────────────────────────────
# set_page_config must be the FIRST Streamlit call in the script.
# The try/except lets this page run both standalone and as part of app.py.
try:
    st.set_page_config(
        page_title="SafeSense AI – Food Complaints",
        page_icon="📢",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
except Exception:
    pass  # Already configured by app.py

# Apply shared global styles (idempotent — safe to call multiple times)
apply_global_styles()


# ─────────────────────────────────────────────────────────────────────────────
# Module-level constants
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_ICONS: dict[str, str] = {
    "Hygiene": "🧹",
    "Food Quality": "🍽️",
    "Expired Food": "⏰",
    "Suspected Adulteration": "⚗️",
    "Foreign Object": "🔍",
    "Packaging": "📦",
    "Mislabeling": "🏷️",
    "Other": "📋",
}

STATUS_COLORS: dict[str, str] = {
    "Submitted":             COLORS["info"],
    "Under Review":          COLORS["warning"],
    "Verification Required": "#E8950F",
    "Action / Response":     COLORS["danger"],
    "Closed":                COLORS["success"],
}

STATUS_ICONS: dict[str, str] = {
    "Submitted":             "📥",
    "Under Review":          "🔎",
    "Verification Required": "📋",
    "Action / Response":     "⚡",
    "Closed":                "✅",
}

# Session-state key prefix (avoids collisions with other modules)
_PFX = "complaint_"


# ─────────────────────────────────────────────────────────────────────────────
# Small HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def _status_color(status: str) -> str:
    return STATUS_COLORS.get(status, COLORS["info"])


def _cat_icon(cat: str) -> str:
    return CATEGORY_ICONS.get(cat, "📋")


def _badge_html(text: str, bg: str, fg: str = "#fff") -> str:
    return (
        f'<span style="display:inline-block;padding:3px 11px;border-radius:999px;'
        f'background:{bg};color:{fg};font-size:0.72rem;font-weight:600;">'
        f'{text}</span>'
    )


def _status_badge_html(status: str) -> str:
    icon = STATUS_ICONS.get(status, "")
    return _badge_html(f"{icon} {status}", _status_color(status))


def _cat_chip_html(cat: str) -> str:
    icon = _cat_icon(cat)
    return (
        f'<span style="display:inline-block;padding:2px 9px;border-radius:8px;'
        f'font-size:0.72rem;font-weight:500;background:{COLORS["mint"]};'
        f'color:{COLORS["dark_teal"]};border:1px solid {COLORS["border"]};">'
        f'{icon} {cat}</span>'
    )


def _id_tag_html(cid: str) -> str:
    return (
        f'<span style="font-family:monospace;font-size:0.72rem;'
        f'color:{COLORS["muted_text"]};background:{COLORS["soft_grey"]};'
        f'padding:2px 7px;border-radius:5px;">{cid}</span>'
    )


def _section_header_html(title: str, subtitle: str = "") -> str:
    sub = (
        f'<p style="margin:2px 0 0 0;color:{COLORS["muted_text"]};'
        f'font-size:0.8rem;">{subtitle}</p>'
        if subtitle else ""
    )
    return (
        f'<div style="border-left:4px solid {COLORS["emerald"]};'
        f'padding-left:0.75rem;margin:1.4rem 0 0.8rem 0;">'
        f'<h3 style="margin:0;color:{COLORS["dark_teal"]};font-size:1rem;'
        f'font-weight:600;">{title}</h3>{sub}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Complaint-specific CSS (extends shared theme — does NOT override it)
# All color values come from COLORS to stay consistent.
# ─────────────────────────────────────────────────────────────────────────────

def _inject_styles() -> None:
    c = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* ── Hero banner ─────────────────────────────────── */
        .c-hero {{
            background: linear-gradient(135deg, {c['dark_teal']} 0%, {c['emerald']} 100%);
            border-radius: 18px;
            padding: 2rem 2.5rem;
            color: #fff;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }}
        .c-hero::before {{
            content: '';
            position: absolute;
            top: -50px; right: -50px;
            width: 220px; height: 220px;
            background: rgba(255,255,255,0.05);
            border-radius: 50%;
        }}
        .c-hero::after {{
            content: '';
            position: absolute;
            bottom: -30px; left: 40%;
            width: 150px; height: 150px;
            background: rgba(255,255,255,0.04);
            border-radius: 50%;
        }}
        .c-hero h2 {{
            color: #fff !important;
            font-size: 1.85rem;
            font-weight: 700;
            margin: 0 0 0.3rem 0;
            line-height: 1.25;
        }}
        .c-hero p {{
            color: rgba(255,255,255,0.80);
            margin: 0;
            font-size: 0.9rem;
        }}
        .c-hero-kpis {{
            display: flex;
            gap: 2.5rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        .c-kpi-item .val {{
            font-size: 2.1rem;
            font-weight: 700;
            color: #fff;
            line-height: 1;
        }}
        .c-kpi-item .lbl {{
            font-size: 0.7rem;
            color: rgba(255,255,255,0.68);
            margin-top: 3px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* ── Complaint card ──────────────────────────────── */
        .c-complaint-card {{
            background: {c['white']};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            transition: box-shadow 0.2s ease, transform 0.15s ease;
        }}
        .c-complaint-card:hover {{
            box-shadow: 0 6px 22px rgba(16,60,56,0.10);
            transform: translateY(-1px);
        }}
        .c-cat-icon-box {{
            font-size: 1.5rem;
            flex-shrink: 0;
            width: 2.4rem; height: 2.4rem;
            display: flex; align-items: center; justify-content: center;
            background: {c['mint']};
            border-radius: 10px;
        }}
        .c-card-body {{ flex: 1; min-width: 0; }}
        .c-card-title {{
            font-weight: 600;
            color: {c['text']};
            font-size: 0.92rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .c-card-meta {{
            font-size: 0.77rem;
            color: {c['muted_text']};
            margin-top: 3px;
        }}
        .c-card-right {{ flex-shrink: 0; text-align: right; }}

        /* ── NLP result card ─────────────────────────────── */
        .c-nlp-result {{
            background: linear-gradient(135deg, #F0FBF6 0%, {c['soft_grey']} 100%);
            border: 1.5px solid {c['emerald']};
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin: 0.8rem 0;
        }}
        .c-nlp-label {{
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: {c['emerald']};
            margin-bottom: 4px;
        }}
        .c-nlp-category {{
            font-size: 1.1rem;
            font-weight: 700;
            color: {c['dark_teal']};
        }}
        .c-nlp-keywords {{
            font-size: 0.78rem;
            color: {c['muted_text']};
            margin-top: 4px;
        }}
        .c-conf-bar-wrap {{
            background: {c['border']};
            border-radius: 4px;
            height: 6px;
            margin-top: 8px;
            overflow: hidden;
        }}
        .c-conf-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        /* ── Duplicate warning ───────────────────────────── */
        .c-dup-warn {{
            background: #FFF2F2;
            border: 1.5px solid {c['danger']};
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            margin: 0.8rem 0;
        }}
        .c-dup-title {{
            font-weight: 700;
            color: {c['danger']};
            font-size: 0.88rem;
            margin-bottom: 5px;
        }}
        .c-dup-item {{
            background: {c['white']};
            border: 1px solid #F9C8C8;
            border-radius: 8px;
            padding: 6px 10px;
            margin-top: 6px;
            font-size: 0.8rem;
            color: {c['text']};
        }}

        /* ── Success box ─────────────────────────────────── */
        .c-success-box {{
            background: linear-gradient(135deg, #F0FBF6, {c['mint']});
            border: 2px solid {c['emerald']};
            border-radius: 16px;
            padding: 2rem 1.5rem;
            text-align: center;
            margin: 1rem 0;
        }}
        .c-success-icon {{ font-size: 3.5rem; }}
        .c-success-box h3 {{
            color: {c['dark_teal']} !important;
            margin: 0.5rem 0 0.3rem 0;
            font-size: 1.3rem;
        }}
        .c-success-box .c-complaint-id {{
            font-family: 'Courier New', monospace;
            font-size: 1.1rem;
            font-weight: 700;
            color: {c['emerald']};
            background: {c['white']};
            padding: 6px 18px;
            border-radius: 8px;
            display: inline-block;
            margin: 0.5rem 0;
            border: 1px solid {c['border']};
            letter-spacing: 0.05em;
        }}
        .c-success-box p {{
            color: {c['muted_text']};
            font-size: 0.85rem;
            margin: 0;
        }}

        /* ── Disclaimer banner ───────────────────────────── */
        .c-disclaimer {{
            background: #FFF8E7;
            border: 1px solid {c['warning']};
            border-left: 4px solid {c['warning']};
            border-radius: 10px;
            padding: 0.75rem 1rem;
            font-size: 0.82rem;
            color: #7A5800;
            margin-bottom: 1.2rem;
        }}

        /* ── Empty state ─────────────────────────────────── */
        .c-empty-state {{
            text-align: center;
            padding: 3rem 1rem;
            color: {c['muted_text']};
        }}
        .c-empty-state .c-empty-icon {{ font-size: 3rem; margin-bottom: 0.5rem; }}
        .c-empty-state p {{ font-size: 0.9rem; }}

        /* ── Status timeline ─────────────────────────────── */
        .c-status-timeline {{
            display: flex;
            align-items: center;
            gap: 4px;
            flex-wrap: wrap;
            margin: 0.6rem 0;
        }}
        .c-status-step {{
            font-size: 0.68rem;
            padding: 3px 9px;
            border-radius: 999px;
            font-weight: 500;
            white-space: nowrap;
        }}
        .c-status-arrow {{
            color: {c['muted_text']};
            font-size: 0.75rem;
        }}

        /* ── Admin stat mini-card ────────────────────────── */
        .c-admin-stat {{
            background: {c['white']};
            border: 1px solid {c['border']};
            border-radius: 10px;
            padding: 0.65rem;
            text-align: center;
        }}
        .c-admin-stat .val {{
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1;
        }}
        .c-admin-stat .lbl {{
            font-size: 0.67rem;
            color: {c['muted_text']};
            font-weight: 500;
            margin-top: 2px;
        }}

        /* ── Tab pill style ──────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px;
            background: {c['soft_grey']};
            border-radius: 12px;
            padding: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 500;
            color: {c['muted_text']};
            background: transparent;
        }}
        .stTabs [aria-selected="true"] {{
            background: {c['white']} !important;
            color: {c['dark_teal']} !important;
            font-weight: 600;
            box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        }}
        .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
        .stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def _tab_dashboard() -> None:
    stats = get_stats()
    complaints = get_all_complaints()
    c = COLORS

    # ── Hero ──────────────────────────────────────────────────────────────────
    open_ct = stats["open"]
    closed_ct = stats["by_status"].get("Closed", 0)
    review_ct = stats["by_status"].get("Under Review", 0)
    sub_ct = stats["by_status"].get("Submitted", 0)

    st.markdown(
        f"""
        <div class="c-hero">
            <h2>📢 Food Complaint Dashboard</h2>
            <p>Monitor, track and manage food safety complaints submitted by consumers.</p>
            <div class="c-hero-kpis">
                <div class="c-kpi-item">
                    <div class="val">{stats['total']}</div>
                    <div class="lbl">Total Filed</div>
                </div>
                <div class="c-kpi-item">
                    <div class="val">{sub_ct}</div>
                    <div class="lbl">Submitted</div>
                </div>
                <div class="c-kpi-item">
                    <div class="val">{review_ct}</div>
                    <div class="lbl">Under Review</div>
                </div>
                <div class="c-kpi-item">
                    <div class="val">{closed_ct}</div>
                    <div class="lbl">Resolved</div>
                </div>
                <div class="c-kpi-item">
                    <div class="val">{open_ct}</div>
                    <div class="lbl">Open</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Charts row ─────────────────────────────────────────────────────────────
    col_chart, col_status = st.columns([3, 2], gap="medium")

    with col_chart:
        st.markdown(
            _section_header_html("📊 Complaints by Category"),
            unsafe_allow_html=True,
        )
        import pandas as pd

        cat_data = {
            f"{_cat_icon(k)} {k}": v
            for k, v in stats["by_category"].items()
            if v > 0
        }
        if cat_data:
            df_cat = pd.DataFrame(
                {"Category": list(cat_data.keys()), "Count": list(cat_data.values())}
            ).set_index("Category")
            st.bar_chart(df_cat, color=c["emerald"])
        else:
            st.caption("No complaint data yet.")

    with col_status:
        st.markdown(
            _section_header_html("🟢 Status Breakdown"),
            unsafe_allow_html=True,
        )
        total = stats["total"] or 1
        for status in COMPLAINT_STATUSES:
            count = stats["by_status"].get(status, 0)
            pct = count / total * 100
            color = _status_color(status)
            icon = STATUS_ICONS.get(status, "")
            st.markdown(
                f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:0.81rem;font-weight:500;color:{c['text']};">
                            {icon} {status}
                        </span>
                        <span style="font-size:0.81rem;color:{c['muted_text']};">
                            {count}
                        </span>
                    </div>
                    <div style="background:{c['border']};border-radius:4px;height:7px;overflow:hidden;">
                        <div style="width:{pct:.1f}%;height:100%;background:{color};
                                    border-radius:4px;transition:width 0.5s ease;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Recent complaints ─────────────────────────────────────────────────────
    st.markdown(
        _section_header_html("🕒 Recent Complaints", "Latest 5 filed complaints"),
        unsafe_allow_html=True,
    )
    recent = sorted(complaints, key=lambda x: x.get("submitted_at", ""), reverse=True)[:5]
    if recent:
        for comp in recent:
            _render_card_mini(comp)
    else:
        st.markdown(
            '<div class="c-empty-state">'
            '<div class="c-empty-icon">📭</div>'
            "<p>No complaints filed yet.</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_card_mini(comp: dict) -> None:
    """Compact card for list/feed views."""
    status = comp.get("status", "Submitted")
    category = comp.get("category", "Other")
    icon = _cat_icon(category)
    date_str = (comp.get("incident_date") or "—")[:10]
    loc = comp.get("location", "—")

    st.markdown(
        f"""
        <div class="c-complaint-card">
            <div class="c-cat-icon-box">{icon}</div>
            <div class="c-card-body">
                <div class="c-card-title">{comp.get('title', 'Untitled')}</div>
                <div class="c-card-meta">
                    {_cat_chip_html(category)}&nbsp;&nbsp;
                    <span>📍 {loc} · 📅 {date_str}</span>
                </div>
                <div style="margin-top:5px;">{_id_tag_html(comp.get('id', '—'))}</div>
            </div>
            <div class="c-card-right">{_status_badge_html(status)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Submit Complaint
# ─────────────────────────────────────────────────────────────────────────────

# Session-state keys used by the submit form
_SK_NLP     = f"{_PFX}nlp_result"
_SK_DUPS    = f"{_PFX}dup_results"
_SK_DONE    = f"{_PFX}submitted_id"
_SK_IMG_N   = f"{_PFX}img_name"
_SK_IMG_B   = f"{_PFX}img_bytes"
_SK_CAT     = f"{_PFX}category"
_SK_TITLE   = f"{_PFX}title"
_SK_DESC    = f"{_PFX}desc"
_SK_LOC     = f"{_PFX}location"
_SK_DATE    = f"{_PFX}date"


def _clear_form() -> None:
    for key in (_SK_NLP, _SK_DUPS, _SK_DONE, _SK_IMG_N, _SK_IMG_B,
                _SK_CAT, _SK_TITLE, _SK_DESC, _SK_LOC, _SK_DATE):
        st.session_state.pop(key, None)


def _tab_submit() -> None:
    c = COLORS

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="c-disclaimer">'
        "<strong>⚠️ Important Notice:</strong> This form records your complaint within "
        "the SafeSense AI system for internal review only. "
        "<strong>Submissions are NOT forwarded to the FSSAI, FDA, or any regulatory "
        "authority.</strong> This tool is for safety monitoring and awareness purposes only."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Success state ─────────────────────────────────────────────────────────
    if st.session_state.get(_SK_DONE):
        cid = st.session_state[_SK_DONE]
        st.markdown(
            f"""
            <div class="c-success-box">
                <div class="c-success-icon">✅</div>
                <h3>Complaint Logged Successfully!</h3>
                <div class="c-complaint-id">{cid}</div>
                <p>Your complaint has been recorded in SafeSense AI.<br>
                   Keep this ID to track the status of your complaint.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        comp = get_complaint_by_id(cid)
        if comp:
            with st.expander("📄 View Submitted Details"):
                _render_complaint_detail(comp)
        if st.button("➕ Submit Another Complaint", key="btn_another"):
            _clear_form()
            st.rerun()
        return

    # ── STEP 1 : Basic Details ────────────────────────────────────────────────
    st.markdown(
        _section_header_html(
            "📝 Complaint Details",
            "Describe the food safety issue clearly and precisely.",
        ),
        unsafe_allow_html=True,
    )

    title = st.text_input(
        "Complaint Title *",
        placeholder="e.g. Found cockroach in packaged food from XYZ store",
        key=_SK_TITLE,
        help="Provide a short, specific title (at least 10 characters).",
    )

    description = st.text_area(
        "Detailed Description *",
        placeholder=(
            "Describe what happened: when, where, what product, brand, store name, "
            "and any other relevant details…"
        ),
        height=135,
        key=_SK_DESC,
        help="More detail helps investigators act faster (minimum 30 characters).",
    )

    # ── STEP 2 : AI Category Detection (before category selector) ─────────────
    st.markdown(
        _section_header_html(
            "🤖 AI Category Detection",
            "Let NLP analyse your text and suggest the right category.",
        ),
        unsafe_allow_html=True,
    )

    col_btn, col_hint = st.columns([2, 5])
    with col_btn:
        run_nlp = st.button(
            "🔍 Auto-detect Category",
            key="btn_nlp_detect",
            help="Analyses title + description to suggest the best category.",
        )
    with col_hint:
        st.caption("Click after entering the title and description above.")

    if run_nlp:
        t = st.session_state.get(_SK_TITLE, "").strip()
        d = st.session_state.get(_SK_DESC, "").strip()
        if not t or not d:
            st.warning("⚠️ Please enter a title and description first.")
        else:
            with st.spinner("Analysing complaint text…"):
                nlp_result = predict_category(t, d)
                st.session_state[_SK_NLP] = nlp_result
                # Set the category selector to predicted value
                st.session_state[_SK_CAT] = nlp_result["predicted_category"]
                # Run duplicate detection
                all_c = get_all_complaints()
                st.session_state[_SK_DUPS] = find_duplicates(t, d, all_c)
            st.rerun()

    # Show NLP result card
    nlp_result = st.session_state.get(_SK_NLP)
    if nlp_result:
        conf = nlp_result["confidence"]
        conf_pct = int(conf * 100)
        pred_cat = nlp_result["predicted_category"]
        kws = nlp_result.get("top_keywords", [])
        kw_str = ", ".join(kws) if kws else "general context"
        conf_color = (
            c["success"] if conf >= 0.60
            else c["warning"] if conf >= 0.35
            else c["muted_text"]
        )
        conf_label = (
            "High confidence" if conf >= 0.60
            else "Moderate confidence" if conf >= 0.35
            else "Low confidence — please select manually"
        )
        st.markdown(
            f"""
            <div class="c-nlp-result">
                <div class="c-nlp-label">🤖 NLP Prediction</div>
                <div class="c-nlp-category">{_cat_icon(pred_cat)} {pred_cat}</div>
                <div class="c-nlp-keywords">Key signals: <em>{kw_str}</em></div>
                <div class="c-conf-bar-wrap">
                    <div class="c-conf-bar-fill"
                         style="width:{conf_pct}%;
                                background:linear-gradient(90deg,{conf_color},{c['info']});">
                    </div>
                </div>
                <div style="font-size:0.74rem;color:{conf_color};margin-top:4px;">
                    Confidence: {conf_pct}% &nbsp;·&nbsp; {conf_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if conf > 0:
            st.caption(
                f"💡 Category pre-filled as **{pred_cat}**. "
                "You can change it in the selector below."
            )

    # Show duplicate warning
    dup_results = st.session_state.get(_SK_DUPS)
    if dup_results:
        dup_items_html = ""
        for d_item in dup_results:
            sim_pct = int(d_item["similarity"] * 100)
            dup_items_html += (
                f'<div class="c-dup-item">'
                f"<strong>{d_item['title']}</strong>"
                f'<span style="float:right;color:{COLORS["danger"]};font-size:0.78rem;">'
                f"{sim_pct}% similar</span><br/>"
                f'<code style="font-size:0.73rem;">{d_item["complaint_id"]}</code>'
                f"</div>"
            )
        st.markdown(
            f"""
            <div class="c-dup-warn">
                <div class="c-dup-title">⚠️ Similar Complaints Already Exist</div>
                <div style="font-size:0.81rem;color:{COLORS['text']};margin-bottom:4px;">
                    The following complaints may be related to yours.
                    Please review before submitting to avoid duplicates.
                </div>
                {dup_items_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("You may still submit if your complaint is genuinely different.")

    # ── STEP 3 : Category, Location, Date ────────────────────────────────────
    st.markdown(
        _section_header_html("📋 Classification & Location"),
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        # Determine safe default index
        current_cat = st.session_state.get(_SK_CAT, "Other")
        default_idx = CATEGORIES.index(current_cat) if current_cat in CATEGORIES else 7

        category = st.selectbox(
            "Category *",
            options=CATEGORIES,
            index=default_idx,
            key=_SK_CAT,
            format_func=lambda x: f"{_cat_icon(x)}  {x}",
            help="Select the most appropriate category for this complaint.",
        )
    with col2:
        location = st.text_input(
            "Location / City *",
            placeholder="e.g. Mumbai, Maharashtra",
            key=_SK_LOC,
        )

    col3, col4 = st.columns(2)
    with col3:
        incident_date = st.date_input(
            "Incident Date *",
            value=st.session_state.get(_SK_DATE, date.today()),
            max_value=date.today(),
            key=_SK_DATE,
            help="Select the date when the incident occurred.",
        )
    with col4:
        st.markdown(
            f'<div style="padding-top:1.8rem;font-size:0.8rem;color:{c["muted_text"]};">'
            "✱ All fields marked * are required."
            "</div>",
            unsafe_allow_html=True,
        )

    # ── STEP 4 : Evidence upload ──────────────────────────────────────────────
    st.markdown(
        _section_header_html(
            "📷 Evidence Upload",
            "Optional — attach an image as supporting evidence.",
        ),
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload image (JPG / PNG / WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        key="cf_file_upload",
        label_visibility="visible",
    )
    if uploaded is not None:
        img_bytes = uploaded.getvalue()
        st.session_state[_SK_IMG_N] = uploaded.name
        st.session_state[_SK_IMG_B] = img_bytes
        col_img, _ = st.columns([2, 3])
        with col_img:
            st.image(img_bytes, caption=f"📎 {uploaded.name}", use_container_width=True)
        st.success(f"✅ Image attached: **{uploaded.name}**")

    # ── Submit ────────────────────────────────────────────────────────────────
    st.markdown("---")
    col_sub, col_clr, _ = st.columns([2, 1, 2])
    with col_sub:
        submit_clicked = st.button(
            "📤 Submit Complaint",
            key="btn_submit",
            type="primary",
            use_container_width=True,
        )
    with col_clr:
        if st.button("🗑️ Clear Form", key="btn_clear", use_container_width=True):
            _clear_form()
            st.rerun()

    if submit_clicked:
        t_val = st.session_state.get(_SK_TITLE, "").strip()
        d_val = st.session_state.get(_SK_DESC, "").strip()
        l_val = st.session_state.get(_SK_LOC, "").strip()
        date_val = st.session_state.get(_SK_DATE, date.today())
        cat_val = st.session_state.get(_SK_CAT, "Other")

        errors: list[str] = []
        if not t_val:
            errors.append("Complaint title is required.")
        elif len(t_val) < 10:
            errors.append("Title must be at least 10 characters.")
        if not d_val:
            errors.append("Detailed description is required.")
        elif len(d_val) < 30:
            errors.append("Description must be at least 30 characters.")
        if not l_val:
            errors.append("Location is required.")

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        else:
            nlp_r = st.session_state.get(_SK_NLP) or {}
            saved = submit_complaint(
                title=t_val,
                description=d_val,
                category=cat_val,
                location=l_val,
                incident_date=date_val,
                image_filename=st.session_state.get(_SK_IMG_N),
                image_bytes=st.session_state.get(_SK_IMG_B),
                nlp_predicted=bool(nlp_r),
                nlp_confidence=float(nlp_r.get("confidence", 0.0)),
            )
            # Store only the ID, then clear intermediate state
            cid = saved["id"]
            _clear_form()
            st.session_state[_SK_DONE] = cid
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Shared complaint detail renderer
# ─────────────────────────────────────────────────────────────────────────────

def _render_status_timeline(current: str) -> None:
    all_s = list(COMPLAINT_STATUSES)
    cur_idx = all_s.index(current) if current in all_s else 0
    parts: list[str] = []
    for i, s in enumerate(all_s):
        color = _status_color(s)
        if i < cur_idx:
            style = f"background:{color};color:#fff;"
        elif i == cur_idx:
            style = (
                f"background:{color};color:#fff;font-weight:700;"
                f"outline:2px solid {COLORS['dark_teal']};outline-offset:2px;"
            )
        else:
            style = f"background:{COLORS['soft_grey']};color:{COLORS['muted_text']};"
        parts.append(f'<span class="c-status-step" style="{style}">{s}</span>')
        if i < len(all_s) - 1:
            parts.append('<span class="c-status-arrow">›</span>')
    st.markdown(
        f'<div class="c-status-timeline">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_complaint_detail(comp: dict) -> None:
    """Full detail view for a single complaint dict."""
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Complaint ID:** `{comp.get('id', '—')}`")
        st.markdown(
            f"**Category:** {_cat_icon(comp.get('category','Other'))} "
            f"{comp.get('category','—')}"
        )
        st.markdown(f"**Location:** 📍 {comp.get('location', '—')}")
        st.markdown(f"**Incident Date:** {comp.get('incident_date', '—')}")
    with col_b:
        st.markdown(f"**Status:** {comp.get('status', '—')}")
        submitted = (comp.get("submitted_at") or "")[:19].replace("T", " ")
        st.markdown(f"**Submitted:** {submitted} UTC")
        nlp_flag = "✅ Yes" if comp.get("nlp_predicted") else "—"
        conf = int((comp.get("nlp_confidence") or 0) * 100)
        st.markdown(f"**NLP Predicted:** {nlp_flag} ({conf}% confidence)")
    st.markdown(f"**Title:** {comp.get('title', '—')}")
    st.markdown("**Description:**")
    st.info(comp.get("description", "—"))
    if comp.get("admin_notes"):
        st.markdown("**Admin Notes:**")
        st.warning(comp["admin_notes"])
    _render_status_timeline(comp.get("status", "Submitted"))


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — My Complaints
# ─────────────────────────────────────────────────────────────────────────────

def _tab_my_complaints() -> None:
    c = COLORS
    complaints = get_all_complaints()

    st.markdown(
        f'<div style="background:{c["soft_grey"]};border-radius:10px;'
        f'padding:0.55rem 1rem;font-size:0.81rem;color:{c["muted_text"]};'
        f'margin-bottom:1rem;">'
        "<strong>ℹ️ Demo mode:</strong> All complaints are shown here. "
        "In production, only your own submissions will appear."
        "</div>",
        unsafe_allow_html=True,
    )

    # Filters
    col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
    with col_f1:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All"] + list(COMPLAINT_STATUSES),
            key="mc_filter_status",
        )
    with col_f2:
        filter_cat = st.selectbox(
            "Filter by Category",
            ["All"] + CATEGORIES,
            key="mc_filter_cat",
        )
    with col_f3:
        search_q = st.text_input(
            "🔎 Search",
            placeholder="Search by title, location, or ID…",
            key="mc_search",
        )

    # Apply filters
    filtered = complaints
    if filter_status != "All":
        filtered = [x for x in filtered if x.get("status") == filter_status]
    if filter_cat != "All":
        filtered = [x for x in filtered if x.get("category") == filter_cat]
    if search_q.strip():
        q = search_q.strip().lower()
        filtered = [
            x for x in filtered
            if q in x.get("title", "").lower()
            or q in x.get("location", "").lower()
            or q in x.get("id", "").lower()
            or q in x.get("description", "").lower()
        ]

    filtered = sorted(filtered, key=lambda x: x.get("submitted_at", ""), reverse=True)
    st.caption(f"Showing **{len(filtered)}** of **{len(complaints)}** complaints")
    st.markdown("---")

    if not filtered:
        st.markdown(
            '<div class="c-empty-state">'
            '<div class="c-empty-icon">🔍</div>'
            "<p>No complaints match your current filters.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    for comp in filtered:
        status = comp.get("status", "Submitted")
        category = comp.get("category", "Other")
        icon = _cat_icon(category)
        date_str = (comp.get("incident_date") or "—")[:10]
        loc = comp.get("location", "—")

        with st.expander(
            f"{icon}  {comp.get('title', 'Untitled')}  ·  {comp.get('id', '')}",
            expanded=False,
        ):
            st.markdown(
                f"{_status_badge_html(status)} &nbsp; {_cat_chip_html(category)} "
                f"&nbsp; <span style='font-size:0.78rem;color:{c['muted_text']};'>"
                f"📍 {loc} · 📅 {date_str}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("")
            _render_complaint_detail(comp)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 4 — Admin Review
# ─────────────────────────────────────────────────────────────────────────────

def _tab_admin() -> None:
    c = COLORS
    complaints = get_all_complaints()
    stats = get_stats()

    # Auth notice
    st.markdown(
        f'<div style="background:#FFF2F2;border:1px solid {c["danger"]};'
        f'border-left:4px solid {c["danger"]};border-radius:10px;'
        f'padding:0.65rem 1rem;font-size:0.81rem;color:{c["danger"]};'
        f'margin-bottom:1rem;">'
        "🔒 <strong>Admin Review Panel</strong> — In production, this panel "
        "requires admin authentication. Visible here for demo purposes only."
        "</div>",
        unsafe_allow_html=True,
    )

    # Quick stats strip
    stat_cols = st.columns(5)
    for i, status in enumerate(COMPLAINT_STATUSES):
        count = stats["by_status"].get(status, 0)
        color = _status_color(status)
        stat_cols[i].markdown(
            f'<div class="c-admin-stat">'
            f'<div class="val" style="color:{color};">{count}</div>'
            f'<div class="lbl">{status}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Filters
    col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
    with col_f1:
        adm_status = st.selectbox(
            "Filter by Status",
            ["All"] + list(COMPLAINT_STATUSES),
            key="adm_filter_status",
        )
    with col_f2:
        adm_cat = st.selectbox(
            "Filter by Category",
            ["All"] + CATEGORIES,
            key="adm_filter_cat",
        )
    with col_f3:
        adm_search = st.text_input(
            "🔎 Search",
            placeholder="ID, title, location…",
            key="adm_search",
        )

    # Apply filters
    filtered = complaints
    if adm_status != "All":
        filtered = [x for x in filtered if x.get("status") == adm_status]
    if adm_cat != "All":
        filtered = [x for x in filtered if x.get("category") == adm_cat]
    if adm_search.strip():
        q = adm_search.strip().lower()
        filtered = [
            x for x in filtered
            if q in x.get("title", "").lower()
            or q in x.get("id", "").lower()
            or q in x.get("location", "").lower()
        ]

    filtered = sorted(filtered, key=lambda x: x.get("submitted_at", ""), reverse=True)
    st.caption(f"**{len(filtered)}** complaints found")

    for comp in filtered:
        status = comp.get("status", "Submitted")
        category = comp.get("category", "Other")
        icon = _cat_icon(category)

        with st.expander(
            f"{icon}  [{comp.get('id', '—')}]  {comp.get('title', 'Untitled')}",
            expanded=False,
        ):
            col_det, col_act = st.columns([3, 2], gap="medium")

            with col_det:
                st.markdown(
                    f"{_status_badge_html(status)} &nbsp; {_cat_chip_html(category)}",
                    unsafe_allow_html=True,
                )
                st.markdown("")
                st.markdown(f"**📍 Location:** {comp.get('location', '—')}")
                st.markdown(f"**📅 Incident:** {comp.get('incident_date', '—')}")
                submitted = (comp.get("submitted_at") or "")[:19].replace("T", " ")
                st.markdown(f"**🕒 Submitted:** {submitted} UTC")
                st.markdown(f"**Description:** {comp.get('description', '—')}")
                if comp.get("admin_notes"):
                    st.markdown(f"**🗒 Current Notes:** {comp['admin_notes']}")
                st.markdown("**Status Timeline:**")
                _render_status_timeline(status)

            with col_act:
                st.markdown(
                    f'<div style="font-weight:600;color:{c["dark_teal"]};'
                    f'margin-bottom:0.4rem;">⚙️ Update Status</div>',
                    unsafe_allow_html=True,
                )
                cur_idx = (
                    list(COMPLAINT_STATUSES).index(status)
                    if status in COMPLAINT_STATUSES else 0
                )
                new_status = st.selectbox(
                    "New Status",
                    list(COMPLAINT_STATUSES),
                    index=cur_idx,
                    key=f"adm_status_{comp['id']}",
                    label_visibility="collapsed",
                )
                new_notes = st.text_area(
                    "Admin Notes",
                    value=comp.get("admin_notes", ""),
                    height=90,
                    key=f"adm_notes_{comp['id']}",
                    placeholder="Add review notes, actions taken, follow-ups…",
                )
                if st.button(
                    "💾 Save Changes",
                    key=f"adm_save_{comp['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    ok = update_complaint_status(comp["id"], new_status, new_notes)
                    if ok:
                        st.success(f"✅ Complaint **{comp['id']}** updated.")
                        st.rerun()
                    else:
                        st.error("❌ Update failed. Check status value.")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def show() -> None:
    """
    Render the full complaint module.

    Call this from app.py when routing to the Food Complaints page:
        from frontend.pages.complaints import show
        show()
    """
    _inject_styles()

    # Page heading (visible in both standalone and integrated modes)
    st.markdown(
        f'<h1 style="color:{COLORS["dark_teal"]};font-size:1.5rem;'
        f'font-weight:700;margin-bottom:0.2rem;">📢 Food Complaint System</h1>'
        f'<p style="color:{COLORS["muted_text"]};font-size:0.85rem;'
        f'margin-bottom:1.2rem;">'
        "Report food safety issues · Track complaints · Admin review</p>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        ["📊 Dashboard", "📝 Submit Complaint", "📂 My Complaints", "🔒 Admin Review"]
    )
    with tabs[0]:
        _tab_dashboard()
    with tabs[1]:
        _tab_submit()
    with tabs[2]:
        _tab_my_complaints()
    with tabs[3]:
        _tab_admin()


# Run immediately when Streamlit executes this file (standalone mode).
# When imported by app.py, call show() explicitly instead.
show()