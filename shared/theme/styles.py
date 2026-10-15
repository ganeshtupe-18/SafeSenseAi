"""Shared Streamlit styling. Import this in every module/page."""

import streamlit as st
from .colors import COLORS


def apply_global_styles() -> None:
    c = COLORS
    st.markdown(
        f"""
        <style>
          :root {{
            --ss-dark-teal: {c['dark_teal']};
            --ss-emerald: {c['emerald']};
            --ss-mint: {c['mint']};
            --ss-soft-grey: {c['soft_grey']};
            --ss-text: {c['text']};
            --ss-border: {c['border']};
          }}
          .stApp {{ background: var(--ss-mint); color: var(--ss-text); }}
          [data-testid="stSidebar"] {{ background: var(--ss-dark-teal); }}
          [data-testid="stSidebar"] * {{ color: #FFFFFF; }}
          .stButton > button {{
            background: var(--ss-emerald); color: #FFFFFF;
            border: 1px solid var(--ss-emerald); border-radius: 10px;
            padding: 0.55rem 1rem; font-weight: 600;
          }}
          .stButton > button:hover {{
            background: var(--ss-dark-teal); color: #FFFFFF;
            border-color: var(--ss-dark-teal);
          }}
          [data-testid="stMetric"] {{
            background: #FFFFFF; border: 1px solid var(--ss-border);
            padding: 1rem; border-radius: 14px;
          }}
          div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; }}
          h1, h2, h3 {{ color: var(--ss-dark-teal); }}
        </style>
        """,
        unsafe_allow_html=True,
    )
