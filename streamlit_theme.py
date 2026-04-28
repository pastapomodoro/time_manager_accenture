"""Stile condiviso: palette unica lime/sage e tipografia leggibile."""

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
<style>
    :root {
        --brand-950: #1A2E05;
        --brand-800: #3F6212;
        --brand-700: #65A30D;
        --brand-500: #84CC16;
        --brand-100: #ECFCCB;
        --brand-50: #F7FEE7;
        --surface: #FFFFFF;
        --border: #D9F99D;
        --muted: #4D5F34;
    }
    h1 {
        font-weight: 600 !important;
        letter-spacing: -0.03em !important;
        color: var(--brand-950) !important;
        margin-bottom: 0.25rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: var(--brand-800) !important;
    }
    [data-testid="stCaptionContainer"] {
        color: var(--muted) !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, var(--brand-50) 0%, #F2FBD8 55%, var(--brand-100) 100%);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--brand-950) !important;
    }
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.25rem 0;
    }
    [data-testid="stMetricValue"] {
        color: var(--brand-700) !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
    }
    .stExpander summary {
        font-weight: 500;
        color: var(--brand-800);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }
    /* Area compilazione: container con key=job_qty_editor (vedi ai_team_estimator) */
    div.st-key-job_qty_editor {
        border: 2px solid var(--brand-500) !important;
        background: rgba(132, 204, 22, 0.08) !important;
        border-radius: 12px !important;
        padding: 0.65rem 0.75rem 0.85rem !important;
        box-shadow: inset 0 0 0 1px rgba(132, 204, 22, 0.16);
    }
</style>
        """,
        unsafe_allow_html=True,
    )
