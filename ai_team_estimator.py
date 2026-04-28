"""
AI_Team Estimator — stima tempi e costi per AI_Team, Accenture Song.
Run: python3 -m streamlit run ai_team_estimator.py
"""

import os, json, html, math
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
                    save_session_tokens, clear_saved_session, restore_saved_session,
                    load_subcontractors_db, save_subcontractors_db)
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
          <p>Estimate time, costs and resources for your AI team</p>
        </div>
        """, unsafe_allow_html=True)

        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                st.markdown("**Sign in to your account**")
                email = st.text_input("Email", placeholder="name@accenture.com", label_visibility="collapsed")
                pwd   = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                remember_me = st.checkbox("Remember me", value=st.session_state.remember_me)
                if st.form_submit_button("Sign in", use_container_width=True):
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
                        st.error("Invalid credentials")
            if st.button("No account? Register →", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()
        else:
            with st.form("signup_form"):
                st.markdown("**Create your account**")
                new_email = st.text_input("Email", placeholder="name@accenture.com", label_visibility="collapsed")
                new_pwd   = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                new_pwd2  = st.text_input("Confirm password", type="password", placeholder="Confirm password", label_visibility="collapsed")
                if st.form_submit_button("Create account", use_container_width=True):
                    if not new_email or not new_pwd:
                        st.error("Please fill in all fields")
                    elif not new_email.lower().endswith("@accenture.com"):
                        st.error("Registration is restricted to @accenture.com accounts")
                    elif new_pwd != new_pwd2:
                        st.error("Passwords do not match")
                    else:
                        try:
                            res = sign_up(new_email, new_pwd)
                            if res.session:
                                st.session_state.sb_session = res.session
                                st.rerun()
                            else:
                                st.success("Check your email to confirm, then sign in.")
                        except Exception as e:
                            st.error(f"Error: {e}")
            if st.button("← Already have an account? Sign in", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
        st.stop()

ORE_GIORNATA     = 8.0
RETRY_MULTIPLIER = 3
SUBCO_COLOR      = "#EC4899"

_XLSX_ENV = os.environ.get("AI_TEAM_DATA_XLSX", "").strip()
DEFAULT_XLSX = (
    os.path.abspath(os.path.expanduser(os.path.normpath(_XLSX_ENV)))
    if _XLSX_ENV
    else os.path.join(os.path.dirname(__file__), "ai_team_data.xlsx")
)
PRESETS_FILE  = os.path.join(os.path.dirname(__file__), "presets.json")
PROFILES_FILE = os.path.join(os.path.dirname(__file__), "profiles.json")
SUBCO_FILE    = os.path.join(os.path.dirname(__file__), "subcontractors.json")

PALETTE = ["#7C3AED","#2563EB","#059669","#D97706","#DC2626",
           "#0891B2","#65A30D","#C026D3","#EA580C","#0F766E"]

RUOLI_OPTIONS     = ["Senior Graphic Designer","Intern",
                     "Video Editor","Art Director","Motion Designer","Retoucher","Altro"]
SENIORITY_OPTIONS = ["junior","mid","senior","lead"]
SKILL_OPTIONS     = ["retouch","compositing","lighting","prompt","video","editing",
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

/* ── COST BREAKDOWN ──────────────────────────────────────── */
.cost-breakdown {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) - 2px);
  padding: 14px 16px;
  margin-top: 12px;
}
.cost-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 13px;
  color: var(--fg);
}
.cost-row-label { color: var(--muted-fg); font-size: 12px; }
.cost-row-tag {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; padding: 2px 7px; border-radius: 999px;
  background: var(--accent); color: var(--accent-fg); margin-left: 6px;
}
.cost-divider { border-top: 1px solid var(--border); margin: 6px 0; }
.cost-total {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 8px; font-size: 15px; font-weight: 700; color: var(--fg);
}
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
ICO_SUBCO  = _ico('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="23" y1="11" x2="17" y2="11"/><line x1="20" y1="8" x2="20" y2="14"/>')


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
    return '<div class="avatar-row">' + "".join(avatar_html(n, color_map.get(n, "#888")) for n in names) + "</div>"


def compact_avatars_html(names, color_map, max_visible: int = 5) -> str:
    if not names:
        return '<span class="job-settings-subtle">No person selected</span>'
    visible = names[:max_visible]
    extra = len(names) - len(visible)
    avatars = "".join(avatar_html(n, color_map.get(n, "#888"), size=28) for n in visible)
    extra_html = f'<span class="avatar-count">+{extra}</span>' if extra > 0 else ""
    return f'<div class="compact-avatar-row">{avatars}{extra_html}</div>'


def fmt_hours(value: float) -> str:
    return f"{value:.1f} h"


def fmt_currency(value: float) -> str:
    return f"€ {value:,.0f}".replace(",", ".")


def fmt_workdays_ceil(days: float) -> str:
    return f"{max(1, math.ceil(days))} work days"


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
        return '<p class="bento-plan-stat" style="margin-bottom:0;color:var(--muted-fg)">No phase data available.</p>'

    clipped = df.head(max_rows)
    max_effort = float(clipped["ore_effort"].max()) if not clipped.empty else 0.0
    if max_effort <= 0:
        max_effort = 1.0

    rows = []
    for idx, row in clipped.reset_index(drop=True).iterrows():
        phase_name = str(row.get("fase", "OTHER") or "OTHER")
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

def load_subcontractors() -> list[dict]:
    if _USE_SUPABASE:
        try:
            return load_subcontractors_db()
        except Exception:
            pass
    return json.load(open(SUBCO_FILE)) if os.path.exists(SUBCO_FILE) else []

def save_subcontractors(subcos: list[dict]):
    if _USE_SUPABASE:
        try:
            save_subcontractors_db(subcos)
            return
        except Exception:
            pass
    json.dump(subcos, open(SUBCO_FILE, "w"), indent=2, ensure_ascii=False)


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
            "costo_per_unita": clean_float(row.get("costo_per_unita_eur", 0)),
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
            "costo_per_unita": clean_float(row.get("costo_per_unita", 0)),
        })
        merged_rows.append(row)
        used_names.add(nome)

    for row in base_rows:
        if row["nome_lavorazione"] not in used_names:
            merged_rows.append(row)

    return pd.DataFrame(
        merged_rows,
        columns=["sottocategoria", "nome_lavorazione", "skill_richiesta", "unita_ora", "quantita", "assegnato_a", "costo_per_unita"],
    )


# ── LOADER ────────────────────────────────────────────────────
@st.cache_data
def load_lavorazioni(file_bytes: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(BytesIO(file_bytes))
    if "lavorazioni" not in xls.sheet_names:
        raise ValueError("Sheet 'lavorazioni' not found")
    df = pd.read_excel(xls, sheet_name="lavorazioni")
    req = {"tipologia_id","sottocategoria","nome_lavorazione","minuti_per_unita","skill_richiesta"}
    miss = req - set(df.columns)
    if miss:
        raise ValueError(f"Missing columns in 'lavorazioni': {miss}")
    df["minuti_per_unita"] = pd.to_numeric(df["minuti_per_unita"], errors="coerce")
    if "costo_per_unita_eur" not in df.columns:
        df["costo_per_unita_eur"] = 0.0
    else:
        df["costo_per_unita_eur"] = pd.to_numeric(df["costo_per_unita_eur"], errors="coerce").fillna(0.0)
    return df.dropna(subset=["minuti_per_unita"]).reset_index(drop=True)

@st.cache_data
def load_team_from_excel(file_bytes: bytes) -> list[dict]:
    xls = pd.ExcelFile(BytesIO(file_bytes))
    if "team" not in xls.sheet_names:
        raise ValueError("Sheet 'team' not found")
    df = pd.read_excel(xls, sheet_name="team")
    # Support legacy costo_orario → promote to costo_lcr
    if "costo_lcr" not in df.columns:
        df["costo_lcr"] = pd.to_numeric(df.get("costo_orario", 0), errors="coerce").fillna(0)
        df["costo_ucr"] = 0.0
    else:
        df["costo_lcr"] = pd.to_numeric(df["costo_lcr"], errors="coerce").fillna(0)
        df["costo_ucr"] = pd.to_numeric(df.get("costo_ucr", 0), errors="coerce").fillna(0)
    df["disponibilita_h_settimana"] = pd.to_numeric(df["disponibilita_h_settimana"], errors="coerce")
    df = df.dropna(subset=["costo_lcr"]).reset_index(drop=True)
    return df.to_dict("records")

def get_team_df() -> pd.DataFrame:
    """Priority: profiles.json > Excel."""
    profiles = load_profiles()
    if profiles is not None:
        return pd.DataFrame(profiles)
    if file_bytes:
        records = load_team_from_excel(file_bytes)
        return pd.DataFrame(records)
    return pd.DataFrame()


# ── EXPORT ────────────────────────────────────────────────────
def build_export_excel(nome_progetto, job_items, ore_pp, costo_pp_internal, costo_pp_subco,
                       costo_pp_prod, costo_totale, ore_reali_tot, giorni_reali,
                       df_team, chargeable: bool) -> bytes:
    rate_label = "LCR" if chargeable else "UCR (BD)"
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        internal_cost = sum(costo_pp_internal.values())
        subco_cost    = sum(costo_pp_subco.values())
        prod_cost     = sum(costo_pp_prod.values())
        pd.DataFrame([
            {"Field": "Project",           "Value": nome_progetto},
            {"Field": "Date",              "Value": datetime.now().strftime("%d/%m/%Y")},
            {"Field": "Project type",      "Value": "Chargeable (LCR)" if chargeable else "BD / Internal (UCR)"},
            {"Field": "Elapsed MD",        "Value": f"{ore_reali_tot:.1f} h"},
            {"Field": "Working days",      "Value": f"{giorni_reali:.1f}"},
            {"Field": f"Internal team cost [{rate_label}]", "Value": f"€ {internal_cost:,.0f}"},
            {"Field": "Subcontractor cost [LCR]",           "Value": f"€ {subco_cost:,.0f}"},
            {"Field": "Production cost (API) [LCR]",        "Value": f"€ {prod_cost:,.0f}"},
            {"Field": "Total job cost",    "Value": f"€ {costo_totale:,.0f}"},
        ]).to_excel(w, sheet_name="Summary", index=False)

        pd.DataFrame([{
            "Task": it["nome"], "Qty": it["quantita"],
            "Units/hr": it["uph"],
            "Base hours": round(it["quantita"]/it["uph"], 2),
            "Real hours": round(it["quantita"]/it["uph"]/max(len(it["assigned"]),1), 2),
            "Working days": round(it["quantita"]/it["uph"]/max(len(it["assigned"]),1)/ORE_GIORNATA, 2),
            "Assigned to": ", ".join(it["assigned"]),
            "Prod cost (API) €": round(it.get("prod_cost", 0), 2),
        } for it in job_items]).to_excel(w, sheet_name="Tasks", index=False)

        all_names = sorted(set(list(ore_pp.keys())))
        team_rows = []
        for n in all_names:
            is_subco = n in costo_pp_subco or (n not in costo_pp_internal and n in ore_pp)
            ruolo = ""
            if not is_subco and "ruolo" in df_team.columns:
                match = df_team.loc[df_team["nome"]==n, "ruolo"]
                if not match.empty:
                    ruolo = str(match.iloc[0])
            team_rows.append({
                "Name": n,
                "Type": "Subcontractor" if n in costo_pp_subco and n not in costo_pp_internal else "Internal",
                "Role": ruolo,
                "Hours": round(ore_pp.get(n, 0), 2),
                "Days": round(ore_pp.get(n, 0) / ORE_GIORNATA, 2),
                "Rate type": "LCR" if (n in costo_pp_subco and n not in costo_pp_internal) else rate_label,
                "Cost €": round(costo_pp_internal.get(n, 0) + costo_pp_subco.get(n, 0), 2),
            })
        pd.DataFrame(team_rows).to_excel(w, sheet_name="Team", index=False)
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
                "sottocategoria": "GENERATION",
                "nome_lavorazione": "AI Image Generation",
                "minuti_per_unita": 60,
                "skill_richiesta": "prompt",
                "costo_per_unita_eur": 0.0,
            }
        ]).to_excel(w, sheet_name="lavorazioni", index=False)

        pd.DataFrame([
            {
                "id": 1,
                "nome": "Name Surname",
                "ruolo": "Senior Graphic Designer",
                "seniority": "senior",
                "costo_lcr": 15,
                "costo_ucr": 10,
                "skill_tags": "prompt,retouch",
                "disponibilita_h_settimana": 40,
            }
        ]).to_excel(w, sheet_name="team", index=False)

        pd.DataFrame([
            {"sheet": "lavorazioni", "note": "Fill tasks catalogue. `minuti_per_unita` must be numeric. `costo_per_unita_eur` is the API/production cost per unit (0 if no API cost)."},
            {"sheet": "team", "note": "Fill team. `costo_lcr` = chargeable rate, `costo_ucr` = BD/internal rate. `disponibilita_h_settimana` must be numeric. Set role to 'Intern' for zero-cost members."},
        ]).to_excel(w, sheet_name="_instructions", index=False)
    return buf.getvalue()


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.title("AI Team Estimator")
    st.divider()

    uploaded_bytes = None
    if _USE_SUPABASE:
        file_bytes = load_xlsx_from_storage()
        if file_bytes:
            st.caption("Excel loaded from Supabase Storage")
        else:
            st.warning("No Excel file in Supabase bucket.")
            file_bytes = None
    elif os.path.exists(DEFAULT_XLSX):
        with open(DEFAULT_XLSX, "rb") as f:
            file_bytes = f.read()
        if _XLSX_ENV:
            st.caption(f"Excel loaded from: `{DEFAULT_XLSX}`")
        else:
            st.caption("`ai_team_data.xlsx` loaded")
    else:
        file_bytes = None

    b_left, b_right = st.columns([1, 1], gap="small")
    with b_left:
        with st.popover("Replace Excel file", use_container_width=True):
            up = st.file_uploader(
                "Upload new Excel",
                type=["xlsx"],
                key="sidebar_replace_excel",
            )
            if up:
                uploaded_bytes = up.getvalue()
                if _USE_SUPABASE:
                    upload_xlsx_to_storage(uploaded_bytes)
                    st.cache_data.clear()
                    st.toast("File updated")
                    st.rerun()
                else:
                    file_bytes = uploaded_bytes
                    st.toast("Excel file loaded")

    with b_right:
        template_excel = build_template_excel(
            file_bytes
            if file_bytes
            else (open(DEFAULT_XLSX, "rb").read() if os.path.exists(DEFAULT_XLSX) else None)
        )
        st.download_button(
            "Excel Template",
            data=template_excel,
            file_name="ai_team_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if not _USE_SUPABASE and uploaded_bytes:
        file_bytes = uploaded_bytes
    st.caption("Replace current file or download the template.")

    if not file_bytes:
        st.info("Upload the Excel file to get started.")
        st.stop()

    try:
        df_lav = load_lavorazioni(file_bytes)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Team legend
    st.divider()
    st.markdown("**Team**")
    df_team_side = get_team_df()
    if not df_team_side.empty:
        color_map_side = {row["nome"]: PALETTE[i % len(PALETTE)]
                         for i, row in df_team_side.iterrows()}
        has_ruolo = "ruolo" in df_team_side.columns
        for _, row in df_team_side.iterrows():
            c1, c2 = st.columns([1, 5])
            c1.markdown(avatar_html(row["nome"], color_map_side[row["nome"]]), unsafe_allow_html=True)
            label = row["ruolo"] if has_ruolo else row.get("seniority", "")
            c2.caption(f"**{row['nome']}**  \n{label}")

    # Subcontractor legend
    subco_list_side = load_subcontractors()
    if subco_list_side:
        st.markdown("**Subcontractors**")
        for sub in subco_list_side:
            c1, c2 = st.columns([1, 5])
            c1.markdown(avatar_html(sub["nome"], SUBCO_COLOR), unsafe_allow_html=True)
            c2.caption(f"**{sub['nome']}**  \n{sub.get('ruolo','')}")

    if _USE_SUPABASE:
        st.divider()
        st.caption("Internal tool · AI_Team · Accenture Song · Data is confidential · Do not share screenshots or exports outside the team.")
        if st.button("Sign out", use_container_width=True):
            sign_out()
            st.rerun()


# ── TABS ──────────────────────────────────────────────────────
tab_job, tab_profili, tab_subco = st.tabs(["Build Job", "Team Profiles", "Subcontractors"])


# ════════════════════════════════════════════════════════════════
# TAB 1 — BUILD JOB
# ════════════════════════════════════════════════════════════════
with tab_job:
    df_team = get_team_df()
    subco_list = load_subcontractors()
    subco_names = {s["nome"] for s in subco_list}
    subco_rate_map = {s["nome"]: clean_float(s.get("costo_orario", 0)) for s in subco_list}

    if df_team.empty and not subco_list:
        st.warning("No team members found. Go to **Team Profiles** tab to add them.")
        st.stop()

    color_map  = {row["nome"]: PALETTE[i % len(PALETTE)] for i, row in df_team.iterrows()}
    for sname in subco_names:
        color_map[sname] = SUBCO_COLOR

    has_ruolo  = "ruolo" in df_team.columns
    tutti_nomi_internal = df_team["nome"].tolist() if not df_team.empty else []
    tutti_nomi = tutti_nomi_internal + list(subco_names)
    presets    = load_presets()

    # ── Project name + preset ──
    top_l, top_r = st.columns([3, 2])
    with top_l:
        nome_progetto = st.text_input("Project name", placeholder="e.g. Nike FW25 — Video Campaign",
                                      label_visibility="collapsed")
    with top_r:
        pc = st.columns([4, 1, 0.7])
        preset_options = ["— none —"] + list(presets.keys())
        saved_sel = st.session_state.get("preset_sel", "— none —")
        sel_index = preset_options.index(saved_sel) if saved_sel in preset_options else 0
        preset_sel  = pc[0].selectbox("Load preset", preset_options,
                                       index=sel_index,
                                       label_visibility="collapsed")
        load_clicked = pc[1].button("Load", use_container_width=True)
        del_clicked  = pc[2].button("X", use_container_width=True, help="Delete selected preset")

    if "preset_data" not in st.session_state:
        st.session_state.preset_data = {}
    if "job_editor_version" not in st.session_state:
        st.session_state.job_editor_version = 0
    if load_clicked and preset_sel != "— none —":
        st.session_state.preset_data = presets[preset_sel]
        st.session_state.preset_sel = preset_sel
        st.session_state.job_editor_version += 1
        st.toast(f"Preset «{preset_sel}» loaded")
        st.rerun()
    if del_clicked and preset_sel != "— none —":
        if _USE_SUPABASE:
            delete_preset_db(preset_sel)
        else:
            del presets[preset_sel]; save_presets(presets)
        st.session_state.preset_sel = "— none —"
        st.session_state.preset_data = {}
        st.session_state.job_editor_version += 1
        st.toast(f"Preset «{preset_sel}» deleted")
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

    # ── Job type (LCR / UCR) ──
    chargeable_default = bool(preset_meta.get("chargeable", True))
    st.markdown(f'<div class="sec-hdr" style="font-size:1.0rem">{ICO_WRENCH} Job settings</div>', unsafe_allow_html=True)
    job_type_col, s1, s2, s3 = st.columns([1.5, 1.1, 1.1, 2.8])
    with job_type_col:
        job_type = st.radio(
            "Project type",
            options=["Chargeable (LCR)", "BD / Internal (UCR)"],
            index=0 if chargeable_default else 1,
            key="job_type_radio",
            label_visibility="collapsed",
        )
        chargeable = job_type == "Chargeable (LCR)"
    with s1:
        start_date = st.date_input("Start date", value=start_default, key="job_start_date")
    with s2:
        deadline_value = st.date_input("Deadline", value=deadline_default, key="job_deadline")
    with s3:
        team_scope = st.multiselect(
            "Team on job",
            options=tutti_nomi,
            default=team_scope_default,
            format_func=lambda n: (f"{initials(n)}  {n} (SUB)" if n in subco_names else f"{initials(n)}  {n}"),
            placeholder="Select who will work on this job…",
            help="Leave empty to include the whole team.",
            key="job_team_scope",
        )
        display_team_scope = team_scope or tutti_nomi
        st.markdown(compact_avatars_html(display_team_scope, color_map), unsafe_allow_html=True)

    nomi_disponibili_job = team_scope or tutti_nomi

    st.divider()
    st.markdown(f'<div class="sec-hdr">{ICO_CLIP} Tasks</div>', unsafe_allow_html=True)
    st.caption("Set units/hour, quantity and people for each task.")

    preset_rows = preset_to_editor_rows(pd_data, df_lav)
    active_rows = build_editor_rows(df_lav, preset_rows)
    active_rows = active_rows[
        active_rows["nome_lavorazione"].fillna("").astype(str).str.strip() != ""
    ].reset_index(drop=True)

    if not active_rows.empty:
        h1, h2, h3, h4 = st.columns([3.4, 1.7, 1.8, 4.1])
        h1.markdown("`Task`")
        h2.markdown("`Qty`")
        h3.markdown("`Units/hr`")
        h4.markdown("`Assigned to`")

        for row_idx, row in active_rows.iterrows():
            current_names = parse_assigned_people(row.get("assegnato_a", ""), nomi_disponibili_job)
            c1, c2, c3, c4 = st.columns([3.4, 1.7, 1.8, 4.1])

            nome = c1.text_input(
                "Task",
                value=str(row["nome_lavorazione"]),
                key=f"job_name_{st.session_state.job_editor_version}_{row_idx}",
                label_visibility="collapsed",
            )
            qty = c2.number_input(
                "Qty",
                min_value=0,
                step=1,
                value=int(row["quantita"]),
                key=f"job_qty_{st.session_state.job_editor_version}_{row_idx}",
                label_visibility="collapsed",
            )
            uph = c3.number_input(
                "Units/hr",
                min_value=0.1,
                step=0.1,
                value=float(row["unita_ora"]),
                key=f"job_uph_{st.session_state.job_editor_version}_{row_idx}",
                label_visibility="collapsed",
            )
            selected_names = c4.multiselect(
                "Assigned to",
                options=nomi_disponibili_job,
                default=current_names,
                format_func=lambda n: (f"{initials(n)}  {n} (SUB)" if n in subco_names else f"{initials(n)}  {n}"),
                key=f"assign_{st.session_state.job_editor_version}_{row_idx}",
                placeholder="Select one or more people...",
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
        cpu = clean_float(row.get("costo_per_unita", 0))

        if qty > 0 and assigned and uph > 0:
            prod_cost = qty * RETRY_MULTIPLIER * cpu if cpu > 0 else 0.0
            job_items.append({
                "nome": nome,
                "uph": uph,
                "fase": str(row.get("sottocategoria", "")).strip(),
                "quantita": qty,
                "assigned": assigned,
                "costo_per_unita": cpu,
                "prod_cost": prod_cost,
            })

    # ── Save preset ──
    with st.expander("Save as preset"):
        sc = st.columns([3, 1])
        pname = sc[0].text_input("Name", value=nome_progetto or "",
                                  placeholder="e.g. Nike FW25", label_visibility="collapsed")
        if sc[1].button("Save", use_container_width=True):
            if not pname.strip():
                st.warning("Enter a preset name")
            elif active_rows.empty:
                st.warning("No tasks to save")
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
                        "chargeable": chargeable,
                    },
                    "rows": snap_rows,
                }
                if _USE_SUPABASE:
                    save_preset_db(pname.strip(), snap)
                else:
                    presets[pname.strip()] = snap; save_presets(presets)
                st.success(f"Preset «{pname.strip()}» saved")

    # ── Results ──
    st.divider()
    label = f"Results{' — ' + nome_progetto if nome_progetto else ''}"
    st.markdown(f'<div class="sec-hdr" style="font-size:1.3rem">{ICO_FILE} {label}</div>', unsafe_allow_html=True)

    if not job_items:
        st.info("Enter at least one quantity and assign a person to see the estimate.")
    else:
        ore_base_tot = ore_effort_tot = ore_reali_tot = 0.0
        ore_pp: dict[str, float]       = {}
        costo_pp_internal: dict[str, float] = {}
        costo_pp_subco: dict[str, float]    = {}
        costo_pp_prod: dict[str, float]     = {}
        phase_rows = []
        prod_cost_total = 0.0

        for it in job_items:
            ob  = it["quantita"] / it["uph"]
            n   = len(it["assigned"])
            or_ = ob / n
            ore_base_tot   += ob
            ore_effort_tot += ob
            ore_reali_tot  += or_
            prod_cost_total += it.get("prod_cost", 0.0)

            for nome in it["assigned"]:
                ore_pp[nome] = ore_pp.get(nome, 0) + or_

                if nome in subco_names:
                    rate = subco_rate_map.get(nome, 0.0)
                    costo_pp_subco[nome] = costo_pp_subco.get(nome, 0) + or_ * rate
                else:
                    ruolo = ""
                    if has_ruolo and not df_team.empty:
                        match = df_team.loc[df_team["nome"] == nome, "ruolo"]
                        if not match.empty:
                            ruolo = str(match.iloc[0])
                    if ruolo == "Intern":
                        rate = 0.0
                    elif chargeable:
                        lcr_col = df_team.loc[df_team["nome"] == nome, "costo_lcr"] if not df_team.empty else pd.Series()
                        rate = clean_float(lcr_col.iloc[0]) if not lcr_col.empty else 0.0
                    else:
                        ucr_col = df_team.loc[df_team["nome"] == nome, "costo_ucr"] if not df_team.empty else pd.Series()
                        rate = clean_float(ucr_col.iloc[0]) if not ucr_col.empty else 0.0
                    costo_pp_internal[nome] = costo_pp_internal.get(nome, 0) + or_ * rate

            phase = str(it.get("fase") or "").strip() or "OTHER"
            phase_rows.append({"fase": phase, "ore_effort": ob, "ore_reali": or_})

        # Accumulate prod cost per task (summary only, not per-person)
        for it in job_items:
            if it.get("prod_cost", 0) > 0:
                costo_pp_prod[it["nome"]] = costo_pp_prod.get(it["nome"], 0) + it["prod_cost"]

        internal_cost = sum(costo_pp_internal.values())
        subco_cost    = sum(costo_pp_subco.values())
        costo_totale  = internal_cost + subco_cost + prod_cost_total

        giorni_reali  = ore_reali_tot / ORE_GIORNATA
        giorni_effort = ore_effort_tot / ORE_GIORNATA
        nomi_c = {n for it in job_items for n in it["assigned"]}
        giorni_per_persona = []
        for nome in nomi_c:
            ore_persona = float(ore_pp.get(nome, 0.0))
            if ore_persona > 0:
                giorni_per_persona.append(ore_persona / ORE_GIORNATA)
        giorni_cal = max(giorni_per_persona) if giorni_per_persona else None

        phase_df = pd.DataFrame(phase_rows)
        if not phase_df.empty:
            phase_df = (
                phase_df.groupby("fase", as_index=False)[["ore_effort", "ore_reali"]]
                .sum()
                .sort_values("ore_effort", ascending=False)
            )

        days = business_days(start_date, deadline_value)
        scope_people = nomi_disponibili_job
        daily_capacity = (len(scope_people) * ORE_GIORNATA) if scope_people else 0.0
        required_per_day = (ore_effort_tot / days) if days > 0 else None

        rate_label = "LCR" if chargeable else "UCR (BD)"

        # KPI bento row
        st.markdown('<section class="bento-board">', unsafe_allow_html=True)
        st.markdown(
            (
                '<div class="bento-kpis">'
                f'{bento_kpi_html("Elapsed MD", fmt_hours(ore_reali_tot), f"{giorni_reali:.1f} person days")}'
                f'{bento_kpi_html(f"Estimated cost [{rate_label}]", fmt_currency(costo_totale), "Internal + Subco + Production")}'
                f'{bento_kpi_html("Total effort", fmt_hours(ore_effort_tot), f"{giorni_effort:.1f} effort days")}'
                f'{bento_kpi_html("Calendar duration", fmt_workdays_ceil(giorni_cal) if giorni_cal else "—", "Based on current assignments")}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        # Cost breakdown card
        st.markdown(
            (
                '<div class="cost-breakdown">'
                '<div class="bento-card-hdr">'
                '<div class="bento-card-title">Cost breakdown</div>'
                f'<div class="bento-card-tag">{html.escape(rate_label)}</div>'
                '</div>'
                '<div class="cost-row">'
                f'<span>Internal team cost <span class="cost-row-tag">{html.escape(rate_label)}</span></span>'
                f'<strong>{html.escape(fmt_currency(internal_cost))}</strong>'
                '</div>'
                '<div class="cost-row">'
                '<span>Subcontractor cost <span class="cost-row-tag">LCR</span></span>'
                f'<strong>{html.escape(fmt_currency(subco_cost))}</strong>'
                '</div>'
                '<div class="cost-row">'
                f'<span>Production cost (API) <span class="cost-row-tag">LCR</span></span>'
                f'<strong>{html.escape(fmt_currency(prod_cost_total))}</strong>'
                '</div>'
                '<div class="cost-divider"></div>'
                '<div class="cost-total">'
                '<span>TOTAL JOB COST</span>'
                f'<span>{html.escape(fmt_currency(costo_totale))}</span>'
                '</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="bento-row2">', unsafe_allow_html=True)

        c_left, c_right = st.columns([1.55, 1.0])
        with c_left:
            phase_meta = f"{len(phase_df)} phases" if not phase_df.empty else "No phase data"
            st.markdown(
                (
                    '<div class="bento-card">'
                    '<div class="bento-card-hdr">'
                    '<div class="bento-card-title">Effort distribution by phase</div>'
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
                    '<div class="bento-card-title">Plan within deadline</div>'
                    '<div class="bento-card-tag">Capacity check</div>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )
            if days <= 0:
                st.markdown(
                    '<p class="bento-plan-stat">Set a valid <strong>start date</strong> and <strong>deadline</strong>.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    (
                        f'<p class="bento-plan-stat">Window: <strong>{days} working days</strong></p>'
                        f'<p class="bento-plan-stat">Team capacity: <strong>{daily_capacity:.1f} h/day</strong></p>'
                        f'<p class="bento-plan-stat">Required effort: <strong>{required_per_day:.1f} h/day</strong></p>'
                    ),
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Calculate plan", use_container_width=True):
                if daily_capacity <= 0:
                    st.warning("Team capacity is zero. Check availability / Team on job.")
                elif days <= 0:
                    st.warning("The time window is not valid.")
                else:
                    gap = ore_effort_tot - (daily_capacity * days)
                    if gap <= 0:
                        st.success("The team can meet the deadline based on current effort.")
                    else:
                        avg_person_day = ORE_GIORNATA if scope_people else 0
                        extra_people = int((gap / (avg_person_day * days)) + 0.999) if avg_person_day > 0 else None
                        st.warning(f"More capacity needed: ~**{gap:.1f} h** missing by deadline.")
                        if extra_people is not None:
                            st.caption(f"Estimate: add ~**{extra_people}** people (average capacity) or increase availability.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div></section>', unsafe_allow_html=True)

        # ── Breakdown by person ──
        all_assigned = sorted(ore_pp.keys())
        with st.expander("Breakdown by person"):
            bp_rows = []
            for n in all_assigned:
                is_subco = n in subco_names
                is_intern = False
                ruolo = ""
                if not is_subco and has_ruolo and not df_team.empty:
                    match = df_team.loc[df_team["nome"] == n, "ruolo"]
                    if not match.empty:
                        ruolo = str(match.iloc[0])
                        is_intern = ruolo == "Intern"
                cost_val = costo_pp_internal.get(n, 0) + costo_pp_subco.get(n, 0)
                bp_rows.append({
                    "Name": n,
                    "Type": "SUB" if is_subco else ("Intern" if is_intern else "Internal"),
                    "Role": ruolo if not is_subco else next((s.get("ruolo","") for s in subco_list if s["nome"]==n), ""),
                    "Rate": "LCR" if is_subco else ("—" if is_intern else rate_label),
                    "Hours": round(ore_pp[n], 1),
                    "Days": round(ore_pp[n] / ORE_GIORNATA, 1),
                    "Cost": f"€ {cost_val:,.0f}" if cost_val > 0 else "—",
                })
            st.dataframe(pd.DataFrame(bp_rows), hide_index=True, use_container_width=True)

        # ── Breakdown by task ──
        with st.expander("Breakdown by task"):
            bt_rows = []
            for it in job_items:
                row_d = {
                    "Task": it["nome"],
                    "Qty": it["quantita"],
                    "Units/hr": it["uph"],
                    "Base hrs": round(it["quantita"] / it["uph"], 1),
                    "Working days": round(it["quantita"] / it["uph"] / max(len(it["assigned"]), 1) / ORE_GIORNATA, 1),
                    "Assigned to": ", ".join(it["assigned"]),
                }
                if it.get("prod_cost", 0) > 0:
                    row_d["Prod cost (API)"] = f"€ {it['prod_cost']:,.2f} (×{RETRY_MULTIPLIER} retry)"
                bt_rows.append(row_d)
            st.dataframe(pd.DataFrame(bt_rows), hide_index=True, use_container_width=True)

        st.divider()
        all_ore_pp = dict(ore_pp)
        excel_b = build_export_excel(
            nome_progetto or "Estimate",
            job_items,
            all_ore_pp,
            costo_pp_internal,
            costo_pp_subco,
            costo_pp_prod,
            costo_totale,
            ore_reali_tot,
            giorni_reali,
            df_team,
            chargeable,
        )
        st.download_button(
            "Export to Excel",
            data=excel_b,
            file_name=f"estimate_{(nome_progetto or 'job').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ════════════════════════════════════════════════════════════════
# TAB 2 — TEAM PROFILES
# ════════════════════════════════════════════════════════════════
with tab_profili:
    st.markdown(f'<div class="sec-hdr">{ICO_USERS} Team Profiles</div>', unsafe_allow_html=True)
    st.caption("Add, edit or remove team members. Changes override the Excel data.")

    profiles = load_profiles()
    if profiles is None:
        try:
            profiles = load_team_from_excel(file_bytes)
        except Exception:
            profiles = []

    df_prof = pd.DataFrame(profiles) if profiles else pd.DataFrame(
        columns=["id","nome","ruolo","seniority","costo_lcr","costo_ucr","skill_tags","disponibilita_h_settimana"]
    )

    # Ensure minimum columns — migrate costo_orario → costo_lcr if needed
    if "costo_lcr" not in df_prof.columns:
        df_prof["costo_lcr"] = pd.to_numeric(df_prof.get("costo_orario", 0), errors="coerce").fillna(0)
    if "costo_ucr" not in df_prof.columns:
        df_prof["costo_ucr"] = 0.0
    for col in ["nome","ruolo","seniority","skill_tags","disponibilita_h_settimana"]:
        if col not in df_prof.columns:
            df_prof[col] = ""

    st.markdown(f'<div class="sec-hdr" style="font-size:0.95rem;font-weight:600;color:var(--fg)">{ICO_WRENCH} Team members</div>', unsafe_allow_html=True)

    edited_prof = st.data_editor(
        df_prof[["nome","ruolo","seniority","costo_lcr","costo_ucr","skill_tags","disponibilita_h_settimana"]],
        column_config={
            "nome":   st.column_config.TextColumn("Name", width="medium"),
            "ruolo":  st.column_config.SelectboxColumn("Role", options=RUOLI_OPTIONS, width="large"),
            "seniority": st.column_config.SelectboxColumn("Seniority", options=SENIORITY_OPTIONS, width="small"),
            "costo_lcr": st.column_config.NumberColumn("LCR €/h", min_value=0, step=1, width="small"),
            "costo_ucr": st.column_config.NumberColumn("UCR €/h", min_value=0, step=1, width="small"),
            "skill_tags": st.column_config.TextColumn(
                "Skill", width="large",
                help="Comma-separated skills. E.g: retouch,compositing,video"
            ),
            "disponibilita_h_settimana": st.column_config.NumberColumn(
                "H/week", min_value=0, max_value=40, step=4, width="small"
            ),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        height=editor_height(len(df_prof), min_rows=3, row_px=38, chrome_px=90),
        key="prof_editor",
    )

    # Avatar preview
    st.caption("Preview")
    valid_rows = edited_prof[edited_prof["nome"].notna() & (edited_prof["nome"].str.strip() != "")]
    if not valid_rows.empty:
        chips = ""
        for idx, (_, row) in enumerate(valid_rows.iterrows()):
            color = PALETTE[idx % len(PALETTE)]
            full = row["nome"]
            ruolo = str(row.get("ruolo", "")).strip()
            is_intern = ruolo == "Intern"
            chips += (
                f'<div style="display:inline-flex;align-items:center;gap:6px;'
                f'background:oklch(0.9819 0.0181 155.8263);border-radius:20px;padding:4px 10px 4px 4px;margin:3px;">'
                f'{avatar_html(row["nome"], color, size=26)}'
                f'<span style="font-size:13px;font-weight:500">{full}</span>'
                f'<span style="font-size:11px;color:var(--muted-fg)">{ruolo}'
                f'{" · zero cost" if is_intern else ""}'
                f'</span>'
                f'</div>'
            )
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:2px">{chips}</div>', unsafe_allow_html=True)
    else:
        st.caption("No members yet.")

    st.divider()
    sc = st.columns([2, 1, 1])
    if sc[0].button("Save profiles", use_container_width=True, type="primary"):
        clean = edited_prof[edited_prof["nome"].notna() & (edited_prof["nome"].str.strip() != "")].copy()
        clean["costo_lcr"] = pd.to_numeric(clean["costo_lcr"], errors="coerce").fillna(0)
        clean["costo_ucr"] = pd.to_numeric(clean["costo_ucr"], errors="coerce").fillna(0)
        clean["disponibilita_h_settimana"] = pd.to_numeric(
            clean["disponibilita_h_settimana"], errors="coerce").fillna(40)
        clean["id"] = range(1, len(clean)+1)
        save_profiles(clean.to_dict("records"))
        load_team_from_excel.clear()
        st.success("Profiles saved")
        st.rerun()

    if not _USE_SUPABASE:
        if sc[1].button("Restore from Excel", use_container_width=True):
            if os.path.exists(PROFILES_FILE):
                os.remove(PROFILES_FILE)
                st.toast("Profiles restored from Excel")
                st.rerun()
            else:
                st.info("Already using Excel data.")
        if os.path.exists(PROFILES_FILE):
            sc[2].markdown(f'<div class="status-label">{ICO_CHECK} Custom profiles active</div>', unsafe_allow_html=True)
        else:
            sc[2].markdown(f'<div class="status-label">{ICO_FILE} Data from Excel</div>', unsafe_allow_html=True)
    else:
        sc[2].markdown(f'<div class="status-label">{ICO_CHECK} Supabase</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 — SUBCONTRACTORS
# ════════════════════════════════════════════════════════════════
with tab_subco:
    st.markdown(f'<div class="sec-hdr">{ICO_SUBCO} Subcontractors</div>', unsafe_allow_html=True)
    st.caption("External collaborators with a single LCR rate. Shown with a pink avatar in task assignment.")

    subcos = load_subcontractors()
    df_subco = pd.DataFrame(subcos) if subcos else pd.DataFrame(
        columns=["id","nome","ruolo","costo_orario","skill_tags","disponibilita_h_settimana"]
    )
    for col in ["nome","ruolo","costo_orario","skill_tags","disponibilita_h_settimana"]:
        if col not in df_subco.columns:
            df_subco[col] = "" if col in ("nome","ruolo","skill_tags") else 0

    st.markdown(f'<div class="sec-hdr" style="font-size:0.95rem;font-weight:600;color:var(--fg)">{ICO_WRENCH} Subcontractor list</div>', unsafe_allow_html=True)

    edited_subco = st.data_editor(
        df_subco[["nome","ruolo","costo_orario","skill_tags","disponibilita_h_settimana"]],
        column_config={
            "nome":   st.column_config.TextColumn("Name", width="medium"),
            "ruolo":  st.column_config.TextColumn("Role", width="large"),
            "costo_orario": st.column_config.NumberColumn("€/h (LCR)", min_value=0, step=1, width="small"),
            "skill_tags": st.column_config.TextColumn(
                "Skill", width="large",
                help="Comma-separated skills."
            ),
            "disponibilita_h_settimana": st.column_config.NumberColumn(
                "H/week", min_value=0, max_value=40, step=4, width="small"
            ),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        height=editor_height(len(df_subco), min_rows=3, row_px=38, chrome_px=90),
        key="subco_editor",
    )

    # Preview
    st.caption("Preview")
    valid_subco = edited_subco[edited_subco["nome"].notna() & (edited_subco["nome"].str.strip() != "")]
    if not valid_subco.empty:
        chips = ""
        for _, row in valid_subco.iterrows():
            full  = row["nome"]
            ruolo = str(row.get("ruolo", "")).strip()
            chips += (
                f'<div style="display:inline-flex;align-items:center;gap:6px;'
                f'background:#fdf2f8;border:1px solid #fbcfe8;border-radius:20px;padding:4px 10px 4px 4px;margin:3px;">'
                f'{avatar_html(full, SUBCO_COLOR, size=26)}'
                f'<span style="font-size:13px;font-weight:500">{html.escape(full)}</span>'
                f'<span style="font-size:11px;color:#be185d">{html.escape(ruolo)}</span>'
                f'</div>'
            )
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:2px">{chips}</div>', unsafe_allow_html=True)
    else:
        st.caption("No subcontractors yet.")

    st.divider()
    ss = st.columns([2, 1])
    if ss[0].button("Save subcontractors", use_container_width=True, type="primary"):
        clean_s = edited_subco[edited_subco["nome"].notna() & (edited_subco["nome"].str.strip() != "")].copy()
        clean_s["costo_orario"] = pd.to_numeric(clean_s["costo_orario"], errors="coerce").fillna(0)
        clean_s["disponibilita_h_settimana"] = pd.to_numeric(
            clean_s["disponibilita_h_settimana"], errors="coerce").fillna(40)
        clean_s["id"] = range(1, len(clean_s)+1)
        save_subcontractors(clean_s.to_dict("records"))
        st.success("Subcontractors saved")
        st.rerun()

    if not _USE_SUPABASE:
        if ss[1].button("Clear list", use_container_width=True):
            if os.path.exists(SUBCO_FILE):
                os.remove(SUBCO_FILE)
                st.toast("Subcontractor list cleared")
                st.rerun()
