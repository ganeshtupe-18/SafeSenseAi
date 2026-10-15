"""Reusable UI helpers. Keep shared visual patterns here."""

import streamlit as st
from .colors import COLORS


def section_title(title: str, subtitle: str | None = None) -> None:
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def status_badge(label: str, status: str = "info") -> None:
    color_key = {
        "success": "success",
        "warning": "warning",
        "danger": "danger",
        "info": "info",
    }.get(status, "info")
    color = COLORS[color_key]
    st.markdown(
        f'<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
        f'background:{color};color:#fff;font-size:0.8rem;font-weight:600;">'
        f'{label}</span>',
        unsafe_allow_html=True,
    )
