"""Stile condiviso: tema viola sobrio e tipografia leggibile."""

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
<style>
    :root {
        --violet-950: #2E1065;
        --violet-700: #6D28D9;
        --violet-100: #EDE9FE;
        --violet-50: #FAF5FF;
    }
    h1 {
        font-weight: 600 !important;
        letter-spacing: -0.03em !important;
        color: var(--violet-950) !important;
        margin-bottom: 0.25rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #3B2F5C !important;
    }
    [data-testid="stCaptionContainer"] {
        color: #5B5266 !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, #FAF8FF 0%, #F1EBFF 55%, #EDE9FE 100%);
        border-right: 1px solid #DDD6FE;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--violet-950) !important;
    }
    hr {
        border: none;
        border-top: 1px solid #DDD6FE;
        margin: 1.25rem 0;
    }
    [data-testid="stMetricValue"] {
        color: var(--violet-700) !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #5B5266 !important;
    }
    .stExpander summary {
        font-weight: 500;
        color: #3B2F5C;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #E9E4F5;
        border-radius: 8px;
        overflow: hidden;
    }
    /* Area compilazione: container con key=job_qty_editor (vedi ai_team_estimator) */
    div.st-key-job_qty_editor {
        border: 2px solid #6D28D9 !important;
        background: rgba(109, 40, 217, 0.07) !important;
        border-radius: 12px !important;
        padding: 0.65rem 0.75rem 0.85rem !important;
        box-shadow: inset 0 0 0 1px rgba(109, 40, 217, 0.12);
    }
</style>
        """,
        unsafe_allow_html=True,
    )
