"""
AI_Team Estimator — stima tempi e costi per AI_Team, Accenture Song.
Run: python3 -m streamlit run ai_team_estimator.py
"""

import os, json, html
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from datetime import date as _date

try:
    from db import (is_supabase_configured, sign_in, sign_up, sign_out,
                    load_profiles_db, save_profiles_db,
                    load_presets_db, save_preset_db, delete_preset_db,
                    load_xlsx_from_storage, upload_xlsx_to_storage,
                    save_session_tokens, clear_saved_session, restore_saved_session)
    _HAS_SUPABASE = True
except ImportError:
    _HAS_SUPABASE = False

_USE_SUPABASE = _HAS_SUPABASE and is_supabase_configured() if _HAS_SUPABASE else False

# ── CONFIG ────────────────────────────────────────────────────
st.set_page_config(page_title="AI Team Estimator", layout="wide")

# ── AUTH GATE (solo se Supabase configurato) ──────────────────
if _USE_SUPABASE:
    if "sb_session" not in st.session_state:
        st.session_state.sb_session = None
    if "remember_me" not in st.session_state:
        st.session_state.remember_me = True
    if st.session_state.sb_session is None:
        restored_session = restore_saved_session()
        if restored_session is not None:
            st.session_state.sb_session = restored_session
            st.rerun()
    if st.session_state.sb_session is None:
        st.markdown("""
        <style>
        header[data-testid="stHeader"], #MainMenu, footer { display:none }

        /* ── ANIMATED BG ── */
        [data-testid="stAppViewContainer"] {
          background: oklch(0.9892 0.0054 117.9205);
          overflow: hidden;
        }
        [data-testid="stAppViewContainer"]::before {
          content: '';
          position: fixed; inset: 0; z-index: 0;
          background:
            radial-gradient(ellipse 70% 55% at 15% 25%, oklch(0.88 0.18 128 / .30) 0%, transparent 60%),
            radial-gradient(ellipse 55% 70% at 85% 75%, oklch(0.82 0.14 145 / .20) 0%, transparent 60%),
            radial-gradient(ellipse 50% 40% at 55% 5%,  oklch(0.92 0.12 118 / .25) 0%, transparent 55%);
          animation: bgPulse 9s ease-in-out infinite alternate;
        }
        @keyframes bgPulse {
          0%   { opacity: .7; transform: scale(1); }
          100% { opacity: 1;  transform: scale(1.04); }
        }

        /* floating orbs */
        [data-testid="stAppViewContainer"]::after {
          content: '';
          position: fixed; inset: 0; z-index: 0; pointer-events: none;
          background:
            radial-gradient(circle 240px at 8% 82%,  oklch(0.87 0.20 128 / .18) 0%, transparent 70%),
            radial-gradient(circle 180px at 92% 18%, oklch(0.80 0.16 140 / .14) 0%, transparent 70%);
          animation: orbFloat 13s ease-in-out infinite alternate;
        }
        @keyframes orbFloat {
          0%   { transform: translateY(0px) translateX(0px); }
          100% { transform: translateY(-28px) translateX(18px); }
        }

        /* ── LAYOUT ── */
        [data-testid="stMain"] {
          display: flex; align-items: center; justify-content: center;
          min-height: 100vh;
        }
        .block-container {
          max-width: 460px !important;
          padding-top: 0 !important; padding-bottom: 0 !important;
          position: relative; z-index: 10;
          width: 100%;
        }

        /* ── HERO TEXT ── */
        .login-hero {
          text-align: center; margin-bottom: 2.5rem;
          animation: fadeUp .6s ease both;
        }
        .login-hero-badge {
          display: inline-flex; align-items: center; gap: 6px;
          background: oklch(0.8871 0.2122 128.5041 / .18);
          border: 1px solid oklch(0.8871 0.2122 128.5041 / .45);
          border-radius: 100px; padding: 4px 14px;
          font-size: .75rem; font-weight: 600; letter-spacing: .06em;
          color: oklch(0.38 0.14 140); text-transform: uppercase;
          margin-bottom: 1rem;
        }
        .login-hero-badge::before {
          content: ''; width: 6px; height: 6px; border-radius: 50%;
          background: oklch(0.8871 0.2122 128.5041);
          animation: blink 1.5s ease infinite;
        }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
        .login-hero h1 {
          font-size: 2.6rem; font-weight: 800; line-height: 1.1;
          letter-spacing: -.04em; margin: 0 0 .75rem;
          background: linear-gradient(135deg, oklch(0.2077 0.0398 265.7549) 0%, oklch(0.42 0.18 140) 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .login-hero p {
          font-size: .95rem; color: oklch(0.5544 0.0407 257.4166); margin: 0;
        }

        /* ── CARD ── */
        div[data-testid="stForm"] {
          background: oklch(1 0 0 / .75) !important;
          backdrop-filter: blur(20px) saturate(1.6) !important;
          -webkit-backdrop-filter: blur(20px) saturate(1.6) !important;
          border: 1px solid oklch(0.9288 0.0126 255.5078) !important;
          border-radius: 16px !important;
          padding: 2rem !important;
          box-shadow: 0 4px 32px oklch(0 0 0 / .08), inset 0 1px 0 oklch(1 0 0 / .9) !important;
          animation: fadeUp .7s .1s ease both;
        }
        @keyframes fadeUp {
          from { opacity:0; transform: translateY(24px); }
          to   { opacity:1; transform: translateY(0); }
        }

        /* inputs */
        div[data-testid="stForm"] input {
          background: oklch(0.98 0.004 118) !important;
          border: 1px solid oklch(0.9288 0.0126 255.5078) !important;
          border-radius: 8px !important;
          color: oklch(0.2077 0.0398 265.7549) !important;
          transition: border-color .2s, box-shadow .2s !important;
        }
        div[data-testid="stForm"] input::placeholder { color: oklch(0.65 0.02 257) !important; }
        div[data-testid="stForm"] input:focus {
          border-color: oklch(0.8871 0.2122 128.5041) !important;
          box-shadow: 0 0 0 3px oklch(0.8871 0.2122 128.5041 / .2) !important;
        }
        div[data-testid="stForm"] [data-testid="stTextInput"] label,
        div[data-testid="stForm"] [data-testid="stTextInputRootElement"] label {
          display: none !important;
        }
        /* Hide Streamlit enter-to-submit helper text that overlaps placeholders */
        div[data-testid="stForm"] [data-testid="InputInstructions"],
        div[data-testid="stForm"] [data-testid="stInputInstructions"] {
          display: none !important;
        }

        /* card title */
        div[data-testid="stForm"] strong { color: oklch(0.2077 0.0398 265.7549) !important; font-size: 1.05rem !important; }

        /* submit button */
        div[data-testid="stFormSubmitButton"] button {
          background: oklch(0.8871 0.2122 128.5041) !important;
          color: #000 !important; font-weight: 700 !important;
          border: none !important; border-radius: 8px !important;
          letter-spacing: .01em !important;
          transition: filter .15s, transform .15s !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
          filter: brightness(.9) !important;
          transform: translateY(-1px) !important;
        }
        div[data-testid="stFormSubmitButton"] button:active { transform: translateY(0) !important; }

        /* switch link button */
        div[data-testid="stButton"] button {
          background: transparent !important;
          border: none !important; color: oklch(0.5544 0.0407 257.4166) !important;
          font-size: .82rem !important;
        }
        div[data-testid="stButton"] button:hover { color: oklch(0.42 0.18 140) !important; }
        </style>

        <div class="login-hero">
          <h1>AI Team<br>Estimator</h1>
          <p>Stima tempi, costi e risorse del tuo team AI</p>
        </div>
        """, unsafe_allow_html=True)

        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                st.markdown("**Accedi al tuo account**")
                email = st.text_input("Email", placeholder="nome@accenture.com", label_visibility="collapsed")
                pwd   = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                remember_me = st.checkbox("Remember me", value=st.session_state.remember_me)
                if st.form_submit_button("Accedi", use_container_width=True):
                    try:
                        res = sign_in(email, pwd)
                        st.session_state.sb_session = res.session
                        st.session_state.remember_me = remember_me
                        if remember_me:
                            save_session_tokens(res.session)
                        else:
                            clear_saved_session()
                        st.rerun()
                    except Exception:
                        st.error("Credenziali non valide")
            if st.button("Non hai un account? Registrati →", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()
        else:
            with st.form("signup_form"):
                st.markdown("**Crea il tuo account**")
                new_email = st.text_input("Email", placeholder="nome@accenture.com", label_visibility="collapsed")
                new_pwd   = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                new_pwd2  = st.text_input("Conferma password", type="password", placeholder="Conferma password", label_visibility="collapsed")
                if st.form_submit_button("Crea account", use_container_width=True):
                    if not new_email or not new_pwd:
                        st.error("Compila tutti i campi")
                    elif not new_email.lower().endswith("@accenture.com"):
                        st.error("La registrazione è riservata agli account @accenture.com")
                    elif new_pwd != new_pwd2:
                        st.error("Le password non coincidono")
                    else:
                        try:
                            res = sign_up(new_email, new_pwd)
                            if res.session:
                                st.session_state.sb_session = res.session
                                st.rerun()
                            else:
                                st.success("Controlla la email per confermare, poi accedi.")
                        except Exception as e:
                            st.error(f"Errore: {e}")
            if st.button("← Hai già un account? Accedi", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
        st.stop()

ORE_GIORNATA     = 8.0
# Percorso Excel: stessa cartella dello script, oppure file ovunque con env AI_TEAM_DATA_XLSX
_XLSX_ENV = os.environ.get("AI_TEAM_DATA_XLSX", "").strip()
DEFAULT_XLSX = (
    os.path.abspath(os.path.expanduser(os.path.normpath(_XLSX_ENV)))
    if _XLSX_ENV
    else os.path.join(os.path.dirname(__file__), "ai_team_data.xlsx")
)
PRESETS_FILE     = os.path.join(os.path.dirname(__file__), "presets.json")
PROFILES_FILE    = os.path.join(os.path.dirname(__file__), "profiles.json")

PALETTE = ["#7C3AED","#2563EB","#059669","#D97706","#DC2626",
           "#0891B2","#65A30D","#C026D3","#EA580C","#0F766E"]

RUOLI_OPTIONS    = ["Senior Graphic Designer","Junior Graphic Designer",
                    "Video Editor","Art Director","Motion Designer","Retoucher","Altro"]
SENIORITY_OPTIONS = ["junior","mid","senior","lead"]
SKILL_OPTIONS    = ["retouch","compositing","lighting","prompt","video","editing",
                    "color","motion","3d","art direction"]

st.markdown("""
<style>
/* ── THEME TOKENS ─────────────────────────────────────────── */
:root {
  --bg:          oklch(0.9892 0.0054 117.9205);
  --fg:          oklch(0.2077 0.0398 265.7549);
  --card:        oklch(1.0000 0 0);
  --primary:     oklch(0.8871 0.2122 128.5041);
  --primary-fg:  oklch(0 0 0);
  --secondary:   oklch(0.3717 0.0392 257.2870);
  --secondary-fg:oklch(0.9842 0.0034 247.8575);
  --muted:       oklch(0.9683 0.0069 247.8956);
  --muted-fg:    oklch(0.5544 0.0407 257.4166);
  --accent:      oklch(0.9819 0.0181 155.8263);
  --accent-fg:   oklch(0.4479 0.1083 151.3277);
  --border:      oklch(0.9288 0.0126 255.5078);
  --destructive: oklch(0.6368 0.2078 25.3313);
  --primary-hover: oklch(0.82 0.20 128.5);
  --focus-ring: oklch(0.8871 0.2122 128.5041 / 0.25);
  --success:     oklch(0.723 0.192 149.579);
  --empty:       oklch(0.74 0.02 250);
  --radius:      1rem;
}

/* ── GLOBAL ───────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {
  font-family: Inter, system-ui, sans-serif !important;
  letter-spacing: -0.01em;
}
.stApp { background: var(--bg) !important; color: var(--fg) !important; }

/* ── SIDEBAR ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--card) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--fg) !important; }

/* ── HEADINGS ────────────────────────────────────────────── */
h1,h2,h3,h4 { color: var(--fg) !important; font-family: Inter, sans-serif !important; }

/* ── BUTTONS ─────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
  background: var(--muted) !important;
  color: var(--fg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  font-family: Inter, sans-serif !important;
  font-weight: 500 !important;
  transition: background 0.15s;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--border) !important;
}
.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  color: var(--primary-fg) !important;
  border-color: var(--primary) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--primary-hover) !important;
}

/* ── INPUTS ──────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: calc(var(--radius) - 4px) !important;
  color: var(--fg) !important;
  font-family: Inter, sans-serif !important;
}
.stNumberInput button {
  display: none !important;
}
.stNumberInput input[type="number"]::-webkit-outer-spin-button,
.stNumberInput input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.stNumberInput input[type="number"] {
  -moz-appearance: textfield;
  appearance: textfield;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px var(--focus-ring) !important;
}
[data-baseweb="select"] > div {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: calc(var(--radius) - 4px) !important;
}
[data-baseweb="tag"] {
  background: var(--accent) !important;
  color: var(--accent-fg) !important;
  border-radius: 999px !important;
}

/* ── METRICS ─────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 16px 20px !important;
  box-shadow: 0px 8px 20px 0px hsl(0 0% 0% / 0.05) !important;
}
[data-testid="stMetricValue"] { color: var(--fg) !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: var(--muted-fg) !important; }

/* ── EXPANDER ────────────────────────────────────────────── */
[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* ── TABS ────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
  font-family: Inter, sans-serif !important;
  font-weight: 500 !important;
  color: var(--muted-fg) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--fg) !important;
  border-bottom-color: var(--primary) !important;
}

/* ── DATAFRAME ───────────────────────────────────────────── */
[data-testid="stDataFrame"] iframe { border-radius: calc(var(--radius) - 2px) !important; }

/* ── DIVIDER ─────────────────────────────────────────────── */
hr { border-color: var(--border) !important; }

/* ── ALERTS ──────────────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-left-color: var(--primary) !important;
}

/* ── APP COMPONENTS ──────────────────────────────────────── */
.avatar {
  display:inline-flex;align-items:center;justify-content:center;
  width:32px;height:32px;border-radius:50%;
  color:white;font-size:11px;font-weight:700;margin-right:4px;flex-shrink:0;
}
.avatar-row{display:flex;flex-wrap:wrap;align-items:center;gap:2px;margin-top:2px;}
.task-name {font-weight:600;font-size:15px;line-height:1.3;color:var(--fg);}
.group-hdr {
  font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;color:var(--muted-fg);margin:20px 0 4px 0;
}
.profile-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--radius);padding:14px 16px;margin-bottom:10px;
}
.job-settings-card{
  background: linear-gradient(180deg, color-mix(in srgb, var(--card) 92%, var(--accent) 8%) 0%, var(--card) 100%);
  border:1px solid var(--border);
  border-radius:calc(var(--radius) - 2px);
  padding:12px 14px;
  margin:8px 0 10px 0;
}
.job-settings-label{
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:.08em;
  color:var(--muted-fg);
  font-weight:700;
  margin-bottom:4px;
}
.job-settings-value{
  font-size:14px;
  color:var(--fg);
  font-weight:600;
}
.job-settings-subtle{
  font-size:12px;
  color:var(--muted-fg);
}
.compact-avatar-row{
  display:flex;
  align-items:center;
  gap:0;
  min-height:32px;
}
.compact-avatar-row .avatar{
  margin-right:-8px;
  border:2px solid var(--card);
  box-shadow:0 1px 2px hsl(0 0% 0% / 0.06);
}
.avatar-count{
  margin-left:12px;
  font-size:12px;
  color:var(--muted-fg);
  font-weight:600;
}
.sec-hdr{
  display:flex;align-items:center;gap:8px;font-size:1.1rem;
  font-weight:700;margin:12px 0 4px 0;color:var(--fg);
}
.sec-hdr svg{flex-shrink:0;}
.status-label{display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--muted-fg);}
.status-label svg{flex-shrink:0;}

/* ── RESULTS BENTO DASHBOARD ───────────────────────────────── */
.bento-board {
  margin: 4px 0 18px 0;
}
.bento-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
@media (max-width: 1100px) {
  .bento-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.bento-kpi {
  background: linear-gradient(165deg, color-mix(in srgb, var(--card) 88%, var(--primary) 12%) 0%, var(--card) 55%);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) - 4px);
  padding: 14px 16px 16px;
  min-height: 92px;
  box-shadow: 0 1px 0 color-mix(in srgb, var(--fg) 6%, transparent);
}
.bento-kpi-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted-fg);
  margin: 0 0 6px 0;
}
.bento-kpi-value {
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--fg);
  line-height: 1.15;
}
.bento-kpi-sub {
  margin-top: 6px;
  font-size: 12px;
  color: var(--muted-fg);
  font-weight: 500;
}
.bento-row2 {
  display: grid;
  grid-template-columns: 1.55fr 1fr;
  gap: 12px;
  align-items: stretch;
}
@media (max-width: 900px) {
  .bento-row2 { grid-template-columns: 1fr; }
}
.bento-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) - 2px);
  padding: 16px 18px 18px;
  box-shadow: 0 1px 0 color-mix(in srgb, var(--fg) 5%, transparent);
}
.bento-card-hdr {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.bento-card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: -0.02em;
}
.bento-card-tag {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted-fg);
}
.bento-phase-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 52px;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}
.bento-phase-row:last-child { margin-bottom: 0; }
.bento-phase-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bento-phase-track {
  grid-column: 1 / -1;
  height: 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--muted) 35%, var(--card));
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--border) 80%, transparent);
}
.bento-phase-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.35s ease;
}
.bento-phase-val {
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--muted-fg);
  text-align: right;
}
.bento-plan-stat {
  font-size: 13px;
  color: var(--fg);
  margin: 0 0 8px 0;
  line-height: 1.45;
}
.bento-plan-stat strong { color: var(--fg); font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# Lucide SVG snippets (16×16, stroke only)
def _ico(path: str, size: int = 16, color: str = "currentColor") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>')

ICO_CLIP   = _ico('<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>')
ICO_USERS  = _ico('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>')
ICO_DL     = _ico('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>')
ICO_CHECK  = _ico('<polyline points="20 6 9 17 4 12"/>', color="var(--success)")
ICO_FILE   = _ico('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>')
ICO_WRENCH = _ico('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>')


# ── HELPERS ───────────────────────────────────────────────────
def initials(name: str) -> str:
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

def avatar_html(name: str, color: str, size: int = 32) -> str:
    return (f'<span class="avatar" style="background:{color};width:{size}px;height:{size}px;">'
            f'{initials(name)}</span>')

def avatars_html(names, color_map) -> str:
    if not names:
        return '<span style="color:var(--empty);font-size:13px;">—</span>'
    return '<div class="avatar-row">' + "".join(avatar_html(n, color_map[n]) for n in names) + "</div>"


def compact_avatars_html(names, color_map, max_visible: int = 5) -> str:
    if not names:
        return '<span class="job-settings-subtle">Nessuna persona selezionata</span>'
    visible = names[:max_visible]
    extra = len(names) - len(visible)
    avatars = "".join(avatar_html(n, color_map[n], size=28) for n in visible)
    extra_html = f'<span class="avatar-count">+{extra}</span>' if extra > 0 else ""
    return f'<div class="compact-avatar-row">{avatars}{extra_html}</div>'


def fmt_hours(value: float) -> str:
    return f"{value:.1f} h"


def fmt_currency(value: float) -> str:
    return f"€ {value:,.0f}".replace(",", ".")


def bento_kpi_html(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="bento-kpi-sub">{html.escape(sub)}</div>' if sub else ""
    return (
        '<div class="bento-kpi">'
        f'<div class="bento-kpi-label">{html.escape(label)}</div>'
        f'<div class="bento-kpi-value">{html.escape(value)}</div>'
        f"{sub_html}"
        "</div>"
    )


def phase_bars_html(df: pd.DataFrame, max_rows: int = 8) -> str:
    if df.empty:
        return '<p class="bento-plan-stat" style="margin-bottom:0;color:var(--muted-fg)">Nessun dato fase disponibile.</p>'

    clipped = df.head(max_rows)
    max_effort = float(clipped["ore_effort"].max()) if not clipped.empty else 0.0
    if max_effort <= 0:
        max_effort = 1.0

    rows = []
    for idx, row in clipped.reset_index(drop=True).iterrows():
        phase_name = str(row.get("fase", "ALTRO") or "ALTRO")
        effort = float(row.get("ore_effort", 0.0) or 0.0)
        pct = max(4.0, min(100.0, (effort / max_effort) * 100.0)) if effort > 0 else 0.0
        color = PALETTE[idx % len(PALETTE)]
        rows.append(
            '<div class="bento-phase-row">'
            f'<div class="bento-phase-name" title="{html.escape(phase_name)}">{html.escape(phase_name)}</div>'
            f'<div class="bento-phase-val">{effort:.1f}h</div>'
            '<div class="bento-phase-track">'
            f'<div class="bento-phase-fill" style="width:{pct:.1f}%;background:{color}"></div>'
            "</div>"
            "</div>"
        )

    return "".join(rows)


# ── STORAGE ───────────────────────────────────────────────────
def load_presets() -> dict:
    if _USE_SUPABASE:
        return load_presets_db()
    return json.load(open(PRESETS_FILE)) if os.path.exists(PRESETS_FILE) else {}

def save_presets(p: dict):
    if not _USE_SUPABASE:
        json.dump(p, open(PRESETS_FILE, "w"), indent=2, ensure_ascii=False)

def load_profiles() -> list[dict] | None:
    if _USE_SUPABASE:
        try:
            data = load_profiles_db()
            return data if data else None
        except Exception:
            return json.load(open(PROFILES_FILE)) if os.path.exists(PROFILES_FILE) else None
    return json.load(open(PROFILES_FILE)) if os.path.exists(PROFILES_FILE) else None

def save_profiles(profiles: list[dict]):
    if _USE_SUPABASE:
        try:
            save_profiles_db(profiles)
            return
        except Exception:
            pass
    json.dump(profiles, open(PROFILES_FILE, "w"), indent=2, ensure_ascii=False)


def clean_float(value, default: float = 0.0) -> float:
    num = pd.to_numeric(value, errors="coerce")
    return float(default if pd.isna(num) else num)


def clean_int(value, default: int = 0) -> int:
    num = pd.to_numeric(value, errors="coerce")
    return int(default if pd.isna(num) else num)


def editor_height(row_count: int, *, min_rows: int = 1, row_px: int = 35, chrome_px: int = 140) -> int:
    visible_rows = max(row_count, min_rows)
    return chrome_px + row_px * visible_rows


def parse_assigned_people(value: str, valid_names: list[str]) -> list[str]:
    return [
        person for person in [p.strip() for p in str(value or "").split(",")]
        if person and person in valid_names
    ]


def preset_to_editor_rows(preset_data: dict, df_lav: pd.DataFrame) -> list[dict]:
    """Normalizza preset legacy e nuovi preset tabellari verso il formato dell'editor."""
    if not preset_data:
        return []

    if isinstance(preset_data.get("rows"), list):
        return preset_data["rows"]

    meta_map = (
        df_lav[["nome_lavorazione", "sottocategoria", "skill_richiesta", "minuti_per_unita"]]
        .drop_duplicates(subset=["nome_lavorazione"])
        .set_index("nome_lavorazione")
        .to_dict("index")
    )

    rows: list[dict] = []
    for nome, values in preset_data.items():
        meta = meta_map.get(nome, {})
        rows.append({
            "sottocategoria": meta.get("sottocategoria", "CUSTOM"),
            "nome_lavorazione": nome,
            "skill_richiesta": meta.get("skill_richiesta", ""),
            "unita_ora": clean_float(values.get("uph", 0)),
            "quantita": clean_int(values.get("qty", 0)),
            "assegnato_a": ", ".join(values.get("assigned", [])),
        })
    return rows


def preset_to_meta(preset_data: dict) -> dict:
    if not preset_data or "meta" not in preset_data:
        return {}
    return preset_data.get("meta", {}) or {}


def business_days(start: _date, end: _date) -> int:
    """Numero di giorni lavorativi (lun-ven) inclusivi. Ritorna 0 se range invalido."""
    if not start or not end or end < start:
        return 0
    return len(pd.bdate_range(start=start, end=end))


def build_editor_rows(df_lav: pd.DataFrame, preset_rows: list[dict]) -> pd.DataFrame:
    """Crea la tabella stile Excel unendo catalogo base e righe custom del preset."""
    base_rows = [
        {
            "sottocategoria": row["sottocategoria"],
            "nome_lavorazione": row["nome_lavorazione"],
            "skill_richiesta": row["skill_richiesta"],
            "unita_ora": round(60 / row["minuti_per_unita"], 1),
            "quantita": 0,
            "assegnato_a": "",
        }
        for _, row in df_lav.iterrows()
    ]

    base_by_name = {row["nome_lavorazione"]: row for row in base_rows}
    merged_rows: list[dict] = []
    used_names: set[str] = set()

    for preset_row in preset_rows:
        nome = str(preset_row.get("nome_lavorazione", "")).strip()
        if not nome:
            continue
        row = dict(base_by_name.get(nome, {}))
        row.update({
            "sottocategoria": str(preset_row.get("sottocategoria", row.get("sottocategoria", "CUSTOM"))).strip() or "CUSTOM",
            "nome_lavorazione": nome,
            "skill_richiesta": str(preset_row.get("skill_richiesta", row.get("skill_richiesta", ""))).strip(),
            "unita_ora": clean_float(preset_row.get("unita_ora", row.get("unita_ora", 0))),
            "quantita": clean_int(preset_row.get("quantita", row.get("quantita", 0))),
            "assegnato_a": str(preset_row.get("assegnato_a", row.get("assegnato_a", ""))).strip(),
        })
        merged_rows.append(row)
        used_names.add(nome)

    for row in base_rows:
        if row["nome_lavorazione"] not in used_names:
            merged_rows.append(row)

    return pd.DataFrame(
        merged_rows,
        columns=["sottocategoria", "nome_lavorazione", "skill_richiesta", "unita_ora", "quantita", "assegnato_a"],
    )


# ── LOADER ────────────────────────────────────────────────────
@st.cache_data
def load_lavorazioni(file_bytes: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(BytesIO(file_bytes))
    if "lavorazioni" not in xls.sheet_names:
        raise ValueError("Foglio 'lavorazioni' non trovato")
    df = pd.read_excel(xls, sheet_name="lavorazioni")
    req = {"tipologia_id","sottocategoria","nome_lavorazione","minuti_per_unita","skill_richiesta"}
    miss = req - set(df.columns)
    if miss:
        raise ValueError(f"Colonne mancanti in 'lavorazioni': {miss}")
    df["minuti_per_unita"] = pd.to_numeric(df["minuti_per_unita"], errors="coerce")
    return df.dropna(subset=["minuti_per_unita"]).reset_index(drop=True)

@st.cache_data
def load_team_from_excel(file_bytes: bytes) -> list[dict]:
    xls = pd.ExcelFile(BytesIO(file_bytes))
    if "team" not in xls.sheet_names:
        raise ValueError("Foglio 'team' non trovato")
    df = pd.read_excel(xls, sheet_name="team")
    df["costo_orario"] = pd.to_numeric(df["costo_orario"], errors="coerce")
    df["disponibilita_h_settimana"] = pd.to_numeric(df["disponibilita_h_settimana"], errors="coerce")
    df = df.dropna(subset=["costo_orario"]).reset_index(drop=True)
    return df.to_dict("records")

def get_team_df() -> pd.DataFrame:
    """Priorità: profiles.json > Excel."""
    profiles = load_profiles()
    if profiles is not None:
        return pd.DataFrame(profiles)
    if file_bytes:
        records = load_team_from_excel(file_bytes)
        return pd.DataFrame(records)
    return pd.DataFrame()


# ── EXPORT ────────────────────────────────────────────────────
def build_export_excel(nome_progetto, job_items, ore_pp, costo_pp,
                       costo_totale, ore_reali_tot, giorni_reali,
                       df_team) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame([
            {"Campo":"Progetto",      "Valore": nome_progetto},
            {"Campo":"Data",          "Valore": datetime.now().strftime("%d/%m/%Y")},
            {"Campo":"Tempo reale",   "Valore": f"{ore_reali_tot:.1f} h"},
            {"Campo":"Giorni reali",  "Valore": f"{giorni_reali:.1f}"},
            {"Campo":"Costo stimato", "Valore": f"€ {costo_totale:,.0f}"},
        ]).to_excel(w, sheet_name="Riepilogo", index=False)

        pd.DataFrame([{
            "Lavorazione": it["nome"], "Quantità": it["quantita"],
            "Unità/ora": it["uph"],
            "Ore base": round(it["quantita"]/it["uph"], 2),
            "Ore reali": round(it["quantita"]/it["uph"]/len(it["assigned"]), 2),
            "Giorni reali": round(it["quantita"]/it["uph"]/len(it["assigned"])/ORE_GIORNATA, 2),
            "Assegnato a": ", ".join(it["assigned"]),
        } for it in job_items]).to_excel(w, sheet_name="Lavorazioni", index=False)

        pd.DataFrame([{
            "Nome": n,
            "Ruolo": df_team.loc[df_team["nome"]==n,"ruolo"].iloc[0] if "ruolo" in df_team.columns else "",
            "Ore": round(ore_pp[n],2),
            "Giorni": round(ore_pp[n]/ORE_GIORNATA,2),
            "Costo €": round(costo_pp[n],2),
        } for n in sorted(ore_pp)]).to_excel(w, sheet_name="Team", index=False)
    return buf.getvalue()


def build_template_excel(source_bytes: bytes | None = None) -> bytes:
    """Restituisce un template Excel scaricabile e riutilizzabile in upload."""
    if source_bytes:
        return source_bytes

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame([
            {
                "tipologia_id": "CAT-001",
                "sottocategoria": "GENERAZIONE",
                "nome_lavorazione": "Generazione immagine AI",
                "minuti_per_unita": 60,
                "skill_richiesta": "prompt",
            }
        ]).to_excel(w, sheet_name="lavorazioni", index=False)

        pd.DataFrame([
            {
                "id": 1,
                "nome": "Nome Cognome",
                "ruolo": "Senior Graphic Designer",
                "seniority": "senior",
                "costo_orario": 15,
                "skill_tags": "prompt,retouch",
                "disponibilita_h_settimana": 40,
            }
        ]).to_excel(w, sheet_name="team", index=False)

        pd.DataFrame([
            {"foglio": "lavorazioni", "note": "Compila le lavorazioni del catalogo. `minuti_per_unita` deve essere numerico."},
            {"foglio": "team", "note": "Compila il team. `costo_orario` e `disponibilita_h_settimana` devono essere numerici."},
        ]).to_excel(w, sheet_name="_istruzioni", index=False)
    return buf.getvalue()


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.title("AI Team Estimator")
    st.divider()

    uploaded_bytes = None
    if _USE_SUPABASE:
        file_bytes = load_xlsx_from_storage()
        if file_bytes:
            st.caption("Excel caricato da Supabase Storage")
        else:
            st.warning("Nessun Excel nel bucket Supabase.")
            file_bytes = None
    elif os.path.exists(DEFAULT_XLSX):
        with open(DEFAULT_XLSX, "rb") as f:
            file_bytes = f.read()
        if _XLSX_ENV:
            st.caption(f"Excel caricato da: `{DEFAULT_XLSX}`")
        else:
            st.caption("`ai_team_data.xlsx` caricato")
    else:
        file_bytes = None

    b_left, b_right = st.columns([1, 1], gap="small")
    with b_left:
        with st.popover("Sostituisci file Excel", use_container_width=True):
            up = st.file_uploader(
                "Carica nuovo Excel",
                type=["xlsx"],
                key="sidebar_replace_excel",
            )
            if up:
                uploaded_bytes = up.getvalue()
                if _USE_SUPABASE:
                    upload_xlsx_to_storage(uploaded_bytes)
                    st.cache_data.clear()
                    st.toast("File aggiornato")
                    st.rerun()
                else:
                    file_bytes = uploaded_bytes
                    st.toast("File Excel caricato")

    with b_right:
        template_excel = build_template_excel(
            file_bytes
            if file_bytes
            else (open(DEFAULT_XLSX, "rb").read() if os.path.exists(DEFAULT_XLSX) else None)
        )
        st.download_button(
            "Template Excel",
            data=template_excel,
            file_name="ai_team_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if not _USE_SUPABASE and uploaded_bytes:
        file_bytes = uploaded_bytes
    st.caption("Sostituisci file corrente o scarica il template.")

    if not file_bytes:
        st.info("Carica il file Excel per iniziare.")
        st.stop()

    try:
        df_lav = load_lavorazioni(file_bytes)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Legenda team (usa profili aggiornati)
    st.divider()
    st.markdown("**Team**")
    df_team_side = get_team_df()
    if not df_team_side.empty:
        color_map = {row["nome"]: PALETTE[i % len(PALETTE)]
                     for i, row in df_team_side.iterrows()}
        has_ruolo = "ruolo" in df_team_side.columns
        for _, row in df_team_side.iterrows():
            c1, c2 = st.columns([1, 5])
            c1.markdown(avatar_html(row["nome"], color_map[row["nome"]]), unsafe_allow_html=True)
            label = row["ruolo"] if has_ruolo else row.get("seniority","")
            c2.caption(f"**{row['nome']}**  \n{label}")

    if _USE_SUPABASE:
        st.divider()
        if st.button("Esci", use_container_width=True):
            sign_out()
            st.rerun()


# ── TABS ──────────────────────────────────────────────────────
tab_job, tab_profili = st.tabs(["Costruisci il job", "Profili team"])


# ════════════════════════════════════════════════════════════════
# TAB 1 — JOB
# ════════════════════════════════════════════════════════════════
with tab_job:
    df_team = get_team_df()
    if df_team.empty:
        st.warning("Nessun membro nel team. Vai al tab **Profili** per aggiungerli.")
        st.stop()

    color_map  = {row["nome"]: PALETTE[i % len(PALETTE)] for i, row in df_team.iterrows()}
    has_ruolo  = "ruolo" in df_team.columns
    tutti_nomi = df_team["nome"].tolist()
    presets    = load_presets()

    # Nome progetto + preset
    top_l, top_r = st.columns([3, 2])
    with top_l:
        nome_progetto = st.text_input("Nome progetto", placeholder="Es. Nike FW25 — Video Campaign",
                                      label_visibility="collapsed")
    with top_r:
        pc = st.columns([4,1,0.7])
        preset_options = ["— nessuno —"] + list(presets.keys())
        saved_sel = st.session_state.get("preset_sel", "— nessuno —")
        sel_index = preset_options.index(saved_sel) if saved_sel in preset_options else 0
        preset_sel  = pc[0].selectbox("Preset", preset_options,
                                       index=sel_index,
                                       label_visibility="collapsed")
        load_clicked = pc[1].button("Carica", use_container_width=True)
        del_clicked  = pc[2].button("X", use_container_width=True, help="Elimina preset selezionato")

    if "preset_data" not in st.session_state:
        st.session_state.preset_data = {}
    if "job_editor_version" not in st.session_state:
        st.session_state.job_editor_version = 0
    if load_clicked and preset_sel != "— nessuno —":
        st.session_state.preset_data = presets[preset_sel]
        st.session_state.preset_sel = preset_sel
        st.session_state.job_editor_version += 1
        st.toast(f"Preset «{preset_sel}» caricato")
        st.rerun()
    if del_clicked and preset_sel != "— nessuno —":
        if _USE_SUPABASE:
            delete_preset_db(preset_sel)
        else:
            del presets[preset_sel]; save_presets(presets)
        st.session_state.preset_sel = "— nessuno —"
        st.session_state.preset_data = {}
        st.session_state.job_editor_version += 1
        st.toast(f"Preset «{preset_sel}» eliminato")
        st.rerun()
    pd_data = st.session_state.preset_data
    preset_meta = preset_to_meta(pd_data)
    team_scope_default = [
        n for n in preset_meta.get("team_scope", tutti_nomi)
        if n in tutti_nomi
    ] or tutti_nomi
    deadline_default = (
        pd.to_datetime(preset_meta.get("deadline")).date()
        if preset_meta.get("deadline")
        else datetime.now().date()
    )
    start_default = (
        pd.to_datetime(preset_meta.get("start_date")).date()
        if preset_meta.get("start_date")
        else datetime.now().date()
    )
    st.markdown(f'<div class="sec-hdr" style="font-size:1.0rem">{ICO_WRENCH} Impostazioni job</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns([1.1, 1.1, 2.8])
    with s1:
        start_date = st.date_input("Data inizio", value=start_default, key="job_start_date")
    with s2:
        deadline_value = st.date_input("Deadline", value=deadline_default, key="job_deadline")
    with s3:
        team_scope = st.multiselect(
            "Team sul job",
            options=tutti_nomi,
            default=team_scope_default,
            format_func=lambda n: f"{initials(n)}  {n}",
            placeholder="Seleziona chi lavorerà sul job…",
            help="Se non selezioni nessuno, il job usa tutto il team.",
            key="job_team_scope",
        )
        display_team_scope = team_scope or tutti_nomi
        st.markdown(compact_avatars_html(display_team_scope, color_map), unsafe_allow_html=True)

    nomi_disponibili_job = team_scope or tutti_nomi

    st.divider()
    st.markdown(f'<div class="sec-hdr">{ICO_CLIP} Lavorazioni</div>', unsafe_allow_html=True)
    st.caption("Sezione unica modificabile: se aggiorni l'Excel, le lavorazioni qui si sincronizzano automaticamente al reload.")

    preset_rows = preset_to_editor_rows(pd_data, df_lav)
    active_rows = build_editor_rows(df_lav, preset_rows)
    active_rows = active_rows[
        active_rows["nome_lavorazione"].fillna("").astype(str).str.strip() != ""
    ].reset_index(drop=True)

    if not active_rows.empty:
        h1, h2, h3, h4 = st.columns([3.4, 1.7, 1.8, 4.1])
        h1.markdown("`Lavorazione`")
        h2.markdown("`Quantità`")
        h3.markdown("`Unità/ora`")
        h4.markdown("`Assegnato a`")

        for row_idx, row in active_rows.iterrows():
            current_names = parse_assigned_people(row.get("assegnato_a", ""), nomi_disponibili_job)
            c1, c2, c3, c4 = st.columns([3.4, 1.7, 1.8, 4.1])

            nome = c1.text_input(
                "Lavorazione",
                value=str(row["nome_lavorazione"]),
                key=f"job_name_{st.session_state.job_editor_version}_{row_idx}",
                label_visibility="collapsed",
            )
            qty = c2.number_input(
                "Quantità",
                min_value=0,
                step=1,
                value=int(row["quantita"]),
                key=f"job_qty_{st.session_state.job_editor_version}_{row_idx}",
                label_visibility="collapsed",
            )
            uph = c3.number_input(
                "Unità/ora",
                min_value=0.1,
                step=0.1,
                value=float(row["unita_ora"]),
                key=f"job_uph_{st.session_state.job_editor_version}_{row_idx}",
                label_visibility="collapsed",
            )
            selected_names = c4.multiselect(
                "Assegnato a",
                options=nomi_disponibili_job,
                default=current_names,
                format_func=lambda n: f"{initials(n)}  {n}",
                key=f"assign_{st.session_state.job_editor_version}_{row_idx}",
                placeholder="Seleziona una o piu persone...",
                label_visibility="collapsed",
            )

            active_rows.at[row_idx, "nome_lavorazione"] = nome.strip()
            active_rows.at[row_idx, "quantita"] = int(qty)
            active_rows.at[row_idx, "unita_ora"] = float(uph)
            active_rows.at[row_idx, "assegnato_a"] = ", ".join(selected_names)

    job_items = []
    for _, row in active_rows.iterrows():
        nome = str(row.get("nome_lavorazione", "")).strip()
        if not nome:
            continue

        uph = clean_float(row.get("unita_ora"))
        qty = clean_int(row.get("quantita"))
        assigned = parse_assigned_people(row.get("assegnato_a", ""), nomi_disponibili_job)

        if qty > 0 and assigned and uph > 0:
            job_items.append({
                "nome": nome,
                "uph": uph,
                "fase": str(row.get("sottocategoria", "")).strip(),
                "quantita": qty,
                "assigned": assigned,
            })

    # Salva preset
    with st.expander("Salva come preset"):
        sc = st.columns([3,1])
        pname = sc[0].text_input("Nome", value=nome_progetto or "",
                                  placeholder="Es. Nike FW25", label_visibility="collapsed")
        if sc[1].button("Salva", use_container_width=True):
            if not pname.strip():
                st.warning("Inserisci un nome")
            elif active_rows.empty:
                st.warning("Nessuna lavorazione da salvare")
            else:
                snap_rows = []
                for _, row in active_rows.iterrows():
                    nome = str(row["nome_lavorazione"]).strip()
                    if not nome:
                        continue
                    snap_rows.append({
                        "sottocategoria": str(row.get("sottocategoria", "")).strip() or "CUSTOM",
                        "nome_lavorazione": nome,
                        "skill_richiesta": str(row.get("skill_richiesta", "")).strip(),
                        "unita_ora": clean_float(row.get("unita_ora", 0)),
                        "quantita": clean_int(row.get("quantita", 0)),
                        "assegnato_a": str(row.get("assegnato_a", "")).strip(),
                    })
                snap = {
                    "meta": {
                        "start_date": start_date.isoformat(),
                        "deadline": deadline_value.isoformat(),
                        "team_scope": team_scope,
                    },
                    "rows": snap_rows,
                }
                if _USE_SUPABASE:
                    save_preset_db(pname.strip(), snap)
                else:
                    presets[pname.strip()] = snap; save_presets(presets)
                st.success(f"Preset «{pname.strip()}» salvato")

    # Risultati
    st.divider()
    label = f"Stima{' — ' + nome_progetto if nome_progetto else ''}"
    st.markdown(f'<div class="sec-hdr" style="font-size:1.3rem">{ICO_FILE} {label}</div>', unsafe_allow_html=True)

    if not job_items:
        st.info("Inserisci almeno una quantità e assegna una persona per vedere la stima.")
    else:
        ore_base_tot = ore_effort_tot = ore_reali_tot = costo_totale = 0.0
        ore_pp: dict[str,float] = {}; costo_pp: dict[str,float] = {}
        phase_rows = []

        for it in job_items:
            ob = it["quantita"] / it["uph"]
            n  = len(it["assigned"])
            or_ = ob / n
            ore_base_tot += ob; ore_effort_tot += ob; ore_reali_tot += or_
            for nome in it["assigned"]:
                t = float(df_team.loc[df_team["nome"]==nome,"costo_orario"].iloc[0])
                ore_pp[nome]   = ore_pp.get(nome,0)   + or_
                costo_pp[nome] = costo_pp.get(nome,0) + or_ * t
                costo_totale  += or_ * t
            phase = str(it.get("fase") or "").strip() or "ALTRO"
            phase_rows.append({"fase": phase, "ore_effort": ob, "ore_reali": or_})

        giorni_reali  = ore_reali_tot / ORE_GIORNATA
        giorni_effort = ore_effort_tot / ORE_GIORNATA
        nomi_c = {n for it in job_items for n in it["assigned"]}
        cap    = df_team[df_team["nome"].isin(nomi_c)]["disponibilita_h_settimana"].sum()
        giorni_cal = (ore_reali_tot / cap * 5) if cap > 0 else None

        phase_df = pd.DataFrame(phase_rows)
        if not phase_df.empty:
            phase_df = (
                phase_df.groupby("fase", as_index=False)[["ore_effort", "ore_reali"]]
                .sum()
                .sort_values("ore_effort", ascending=False)
            )

        days = business_days(start_date, deadline_value)
        scope_people = nomi_disponibili_job
        daily_capacity = (
            df_team[df_team["nome"].isin(scope_people)]["disponibilita_h_settimana"].sum() / 5.0
            if scope_people else 0.0
        )
        required_per_day = (ore_effort_tot / days) if days > 0 else None

        st.markdown('<section class="bento-board">', unsafe_allow_html=True)
        st.markdown(
            (
                '<div class="bento-kpis">'
                f'{bento_kpi_html("Tempo reale", fmt_hours(ore_reali_tot), f"{giorni_reali:.1f} gg persone")}'
                f'{bento_kpi_html("Costo stimato", fmt_currency(costo_totale), "Basato su costo orario del team")}'
                f'{bento_kpi_html("Effort totale", fmt_hours(ore_effort_tot), f"{giorni_effort:.1f} gg effort")}'
                f'{bento_kpi_html("Durata calendario", f"{giorni_cal:.0f} gg lav." if giorni_cal else "—", "Con assegnazioni attuali")}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
        st.markdown('<div class="bento-row2">', unsafe_allow_html=True)

        c_left, c_right = st.columns([1.55, 1.0])
        with c_left:
            phase_meta = f"{len(phase_df)} fasi" if not phase_df.empty else "Nessuna fase"
            st.markdown(
                (
                    '<div class="bento-card">'
                    '<div class="bento-card-hdr">'
                    '<div class="bento-card-title">Distribuzione effort per fase</div>'
                    f'<div class="bento-card-tag">{html.escape(phase_meta)}</div>'
                    '</div>'
                    f'{phase_bars_html(phase_df)}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with c_right:
            st.markdown(
                (
                    '<div class="bento-card">'
                    '<div class="bento-card-hdr">'
                    '<div class="bento-card-title">Piano entro deadline</div>'
                    '<div class="bento-card-tag">Capacity check</div>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )
            if days <= 0:
                st.markdown(
                    '<p class="bento-plan-stat">Imposta una <strong>data inizio</strong> e una <strong>deadline</strong> valide.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    (
                        f'<p class="bento-plan-stat">Finestra: <strong>{days} gg lavorativi</strong></p>'
                        f'<p class="bento-plan-stat">Capacità team: <strong>{daily_capacity:.1f} h/giorno</strong></p>'
                        f'<p class="bento-plan-stat">Effort richiesto: <strong>{required_per_day:.1f} h/giorno</strong></p>'
                    ),
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Calcola piano", use_container_width=True):
                if daily_capacity <= 0:
                    st.warning("Capacità team nulla. Controlla disponibilità/Team sul job.")
                elif days <= 0:
                    st.warning("La finestra temporale non è valida.")
                else:
                    gap = ore_effort_tot - (daily_capacity * days)
                    if gap <= 0:
                        st.success("Con il team selezionato sei dentro deadline (sulla base dell'effort).")
                    else:
                        avg_person_day = (
                            df_team[df_team["nome"].isin(scope_people)]["disponibilita_h_settimana"].mean() / 5.0
                            if scope_people else 0
                        )
                        extra_people = int((gap / (avg_person_day * days)) + 0.999) if avg_person_day > 0 else None
                        st.warning(f"Serve più capacità: mancano ~**{gap:.1f} h** entro deadline.")
                        if extra_people is not None:
                            st.caption(f"Stima: aggiungi ~**{extra_people}** persone (con capacità media) oppure aumenta disponibilità.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div></section>', unsafe_allow_html=True)

        with st.expander("Dettaglio per persona"):
            st.dataframe(pd.DataFrame([{
                "Nome": n,
                "Ruolo": df_team.loc[df_team["nome"]==n,"ruolo"].iloc[0] if has_ruolo else "",
                "Ore": round(ore_pp[n],1),
                "Giorni": round(ore_pp[n]/ORE_GIORNATA,1),
                "Costo": f"€ {costo_pp[n]:,.0f}",
            } for n in sorted(ore_pp)]), hide_index=True, use_container_width=True)

        with st.expander("Dettaglio per lavorazione"):
            st.dataframe(pd.DataFrame([{
                "Lavorazione": it["nome"], "Qta": it["quantita"], "Unità/ora": it["uph"],
                "Ore base": round(it["quantita"]/it["uph"],1),
                "Giorni reali": round(it["quantita"]/it["uph"]/len(it["assigned"])/ORE_GIORNATA,1),
                "Assegnato a": ", ".join(it["assigned"]),
            } for it in job_items]), hide_index=True, use_container_width=True)

        st.divider()
        excel_b = build_export_excel(nome_progetto or "Stima", job_items,
                                      ore_pp, costo_pp, costo_totale,
                                      ore_reali_tot, giorni_reali, df_team)
        st.download_button(f"Esporta stima in Excel", data=excel_b,
                           file_name=f"stima_{(nome_progetto or 'job').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 — PROFILI
# ════════════════════════════════════════════════════════════════
with tab_profili:
    st.markdown(f'<div class="sec-hdr">{ICO_USERS} Profili team</div>', unsafe_allow_html=True)
    st.caption("Aggiungi, modifica o rimuovi membri del team. Le modifiche sostituiscono i dati dell'Excel.")

    # Carica profili (da JSON o da Excel come base)
    profiles = load_profiles()
    if profiles is None:
        try:
            profiles = load_team_from_excel(file_bytes)
        except Exception:
            profiles = []

    df_prof = pd.DataFrame(profiles) if profiles else pd.DataFrame(
        columns=["id","nome","ruolo","seniority","costo_orario","skill_tags","disponibilita_h_settimana"]
    )

    # Assicura colonne minime
    for col in ["nome","ruolo","seniority","costo_orario","skill_tags","disponibilita_h_settimana"]:
        if col not in df_prof.columns:
            df_prof[col] = ""

    st.markdown(f'<div class="sec-hdr" style="font-size:0.95rem;font-weight:600;color:var(--fg)">{ICO_WRENCH} Membri del team</div>', unsafe_allow_html=True)

    edited_prof = st.data_editor(
        df_prof[["nome","ruolo","seniority","costo_orario","skill_tags","disponibilita_h_settimana"]],
        column_config={
            "nome":   st.column_config.TextColumn("Nome", width="medium"),
            "ruolo":  st.column_config.SelectboxColumn("Ruolo", options=RUOLI_OPTIONS, width="large"),
            "seniority": st.column_config.SelectboxColumn("Seniority",
                                                           options=SENIORITY_OPTIONS, width="small"),
            "costo_orario": st.column_config.NumberColumn("€/ora", min_value=0, step=1, width="small"),
            "skill_tags": st.column_config.TextColumn(
                "Skill", width="large",
                help="Skill separate da virgola. Es: retouch,compositing,video"
            ),
            "disponibilita_h_settimana": st.column_config.NumberColumn(
                "H/settimana", min_value=0, max_value=40, step=4, width="small"
            ),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        height=editor_height(len(df_prof), min_rows=3, row_px=38, chrome_px=90),
        key="prof_editor",
    )

    # Anteprima avatar
    st.caption("Anteprima")
    valid_rows = edited_prof[edited_prof["nome"].notna() & (edited_prof["nome"].str.strip() != "")]
    if not valid_rows.empty:
        chips = ""
        for idx, (_, row) in enumerate(valid_rows.iterrows()):
            color = PALETTE[idx % len(PALETTE)]
            full = row["nome"]
            ruolo = str(row.get("ruolo", "")).strip()
            chips += (
                f'<div style="display:inline-flex;align-items:center;gap:6px;'
                f'background:oklch(0.9819 0.0181 155.8263);border-radius:20px;padding:4px 10px 4px 4px;margin:3px;">'
                f'{avatar_html(row["nome"], color, size=26)}'
                f'<span style="font-size:13px;font-weight:500">{full}</span>'
                f'<span style="font-size:11px;color:var(--muted-fg)">{ruolo}</span>'
                f'</div>'
            )
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:2px">{chips}</div>', unsafe_allow_html=True)
    else:
        st.caption("Nessun membro ancora.")

    st.divider()
    sc = st.columns([2,1,1])
    if sc[0].button("Salva profili", use_container_width=True, type="primary"):
        clean = edited_prof[edited_prof["nome"].notna() & (edited_prof["nome"].str.strip() != "")].copy()
        clean["costo_orario"] = pd.to_numeric(clean["costo_orario"], errors="coerce").fillna(0)
        clean["disponibilita_h_settimana"] = pd.to_numeric(
            clean["disponibilita_h_settimana"], errors="coerce").fillna(40)
        clean["id"] = range(1, len(clean)+1)
        save_profiles(clean.to_dict("records"))
        load_team_from_excel.clear()
        st.success("Profili salvati")
        st.rerun()

    if not _USE_SUPABASE:
        if sc[1].button("Ripristina da Excel", use_container_width=True):
            if os.path.exists(PROFILES_FILE):
                os.remove(PROFILES_FILE)
                st.toast("Profili ripristinati dall'Excel")
                st.rerun()
            else:
                st.info("Stai già usando i dati dall'Excel.")
        if os.path.exists(PROFILES_FILE):
            sc[2].markdown(f'<div class="status-label">{ICO_CHECK} Profili personalizzati attivi</div>', unsafe_allow_html=True)
        else:
            sc[2].markdown(f'<div class="status-label">{ICO_FILE} Dati da Excel</div>', unsafe_allow_html=True)
    else:
        sc[2].markdown(f'<div class="status-label">{ICO_CHECK} Supabase</div>', unsafe_allow_html=True)
