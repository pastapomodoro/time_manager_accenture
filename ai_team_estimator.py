"""
AI_Team Estimator — stima tempi e costi per AI_Team, Accenture Song.
Run: python3 -m streamlit run ai_team_estimator.py
"""

import os, json
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

try:
    from db import (is_supabase_configured, sign_in, sign_up, sign_out,
                    load_profiles_db, save_profiles_db,
                    load_presets_db, save_preset_db, delete_preset_db,
                    load_xlsx_from_storage, upload_xlsx_to_storage)
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
    if st.session_state.sb_session is None:
        st.markdown("""
        <style>
        header[data-testid="stHeader"], #MainMenu, footer { display:none }
        [data-testid="stAppViewContainer"] { background: oklch(0.9892 0.0054 117.9205) }
        .block-container { max-width: 360px !important; padding-top: 6rem !important; }
        div[data-testid="stForm"] {
          background: #fff;
          border: 1px solid oklch(0.9288 0.0126 255.5078);
          border-radius: 12px;
          padding: 2rem !important;
          box-shadow: 0 2px 16px oklch(0 0 0 / .06);
        }
        div[data-testid="stFormSubmitButton"] button {
          background: oklch(0.8871 0.2122 128.5041) !important;
          color: #000 !important; font-weight: 600 !important;
          border: none !important; border-radius: 8px !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover { filter: brightness(.92) !important }
        </style>
        """, unsafe_allow_html=True)

        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        st.markdown("### AI Team Estimator")
        st.markdown("&nbsp;")

        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                st.markdown("**Accedi**")
                email = st.text_input("Email", placeholder="nome@azienda.com", label_visibility="collapsed")
                pwd   = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                if st.form_submit_button("Accedi", use_container_width=True):
                    try:
                        res = sign_in(email, pwd)
                        st.session_state.sb_session = res.session
                        st.rerun()
                    except Exception:
                        st.error("Credenziali non valide")
            if st.button("Non hai un account? Registrati", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()
        else:
            with st.form("signup_form"):
                st.markdown("**Crea account**")
                new_email = st.text_input("Email", placeholder="nome@azienda.com", label_visibility="collapsed")
                new_pwd   = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                new_pwd2  = st.text_input("Conferma password", type="password", placeholder="Conferma password", label_visibility="collapsed")
                if st.form_submit_button("Crea account", use_container_width=True):
                    if not new_email or not new_pwd:
                        st.error("Compila tutti i campi")
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
            if st.button("Hai già un account? Accedi", use_container_width=True):
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
  background: oklch(0.82 0.20 128.5) !important;
}

/* ── INPUTS ──────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: calc(var(--radius) - 4px) !important;
  color: var(--fg) !important;
  font-family: Inter, sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px oklch(0.8871 0.2122 128.5041 / 0.25) !important;
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
.sec-hdr{
  display:flex;align-items:center;gap:8px;font-size:1.1rem;
  font-weight:700;margin:12px 0 4px 0;color:var(--fg);
}
.sec-hdr svg{flex-shrink:0;}
.status-label{display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--muted-fg);}
.status-label svg{flex-shrink:0;}
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
ICO_CHECK  = _ico('<polyline points="20 6 9 17 4 12"/>', color="#16a34a")
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
        return '<span style="color:#bbb;font-size:13px;">—</span>'
    return '<div class="avatar-row">' + "".join(avatar_html(n, color_map[n]) for n in names) + "</div>"


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
        data = load_profiles_db()
        return data if data else None
    return json.load(open(PROFILES_FILE)) if os.path.exists(PROFILES_FILE) else None

def save_profiles(profiles: list[dict]):
    if _USE_SUPABASE:
        save_profiles_db(profiles)
    else:
        json.dump(profiles, open(PROFILES_FILE, "w"), indent=2, ensure_ascii=False)


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


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.title("AI Team Estimator")
    st.divider()

    if _USE_SUPABASE:
        file_bytes = load_xlsx_from_storage()
        if file_bytes:
            st.caption("Excel caricato da Supabase Storage")
            with st.expander("Sostituisci file Excel"):
                up = st.file_uploader("Nuovo Excel", type=["xlsx"])
                if up and st.button("Carica su Supabase", use_container_width=True):
                    upload_xlsx_to_storage(up.getvalue())
                    st.cache_data.clear()
                    st.toast("File aggiornato")
                    st.rerun()
        else:
            st.warning("Nessun Excel nel bucket Supabase.")
            up = st.file_uploader("Carica ai_team_data.xlsx", type=["xlsx"])
            if up and st.button("Carica su Supabase", use_container_width=True):
                upload_xlsx_to_storage(up.getvalue())
                st.rerun()
            file_bytes = up.getvalue() if up else None
        st.divider()
        if st.button("Esci", use_container_width=True):
            sign_out()
            st.rerun()
    elif os.path.exists(DEFAULT_XLSX):
        with open(DEFAULT_XLSX, "rb") as f:
            file_bytes = f.read()
        if _XLSX_ENV:
            st.caption(f"Excel caricato da: `{DEFAULT_XLSX}`")
        else:
            st.caption("`ai_team_data.xlsx` caricato")
        with st.expander("Sostituisci file"):
            up = st.file_uploader("Carica un altro Excel", type=["xlsx"])
            if up:
                file_bytes = up.getvalue()
    else:
        up = st.file_uploader("Carica ai_team_data.xlsx", type=["xlsx"])
        file_bytes = up.getvalue() if up else None

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
    if load_clicked and preset_sel != "— nessuno —":
        st.session_state.preset_data = presets[preset_sel]
        st.session_state.preset_sel = preset_sel
        st.toast(f"Preset «{preset_sel}» caricato")
        st.rerun()
    if del_clicked and preset_sel != "— nessuno —":
        if _USE_SUPABASE:
            delete_preset_db(preset_sel)
        else:
            del presets[preset_sel]; save_presets(presets)
        st.session_state.preset_sel = "— nessuno —"
        st.toast(f"Preset «{preset_sel}» eliminato")
        st.rerun()
    pd_data = st.session_state.preset_data

    st.divider()
    st.markdown(f'<div class="sec-hdr">{ICO_CLIP} Lavorazioni</div>', unsafe_allow_html=True)
    st.caption("Imposta unità/ora, quantità e persone per ogni lavorazione del job.")

    hcols = st.columns([3, 1.2, 1, 3, 1.8])
    for col, lbl in zip(hcols, ["Lavorazione","Unità/ora","Quantità","Assegnato a",""]):
        col.markdown(f"<span style='font-size:12px;font-weight:700;color:#888'>{lbl}</span>",
                     unsafe_allow_html=True)
    st.markdown("<hr style='margin:4px 0 8px 0'>", unsafe_allow_html=True)

    job_items = []
    for gruppo_nome, gruppo_df in df_lav.groupby("sottocategoria", sort=False):
        st.markdown(f'<div class="group-hdr">{gruppo_nome}</div>', unsafe_allow_html=True)
        for i, lav in gruppo_df.iterrows():
            p   = pd_data.get(lav["nome_lavorazione"], {})
            uph_def = round(60 / lav["minuti_per_unita"], 1)
            cn, cm, cq, ct, ca = st.columns([3, 1.2, 1, 3, 1.8])
            with cn:
                st.markdown(f'<div class="task-name">{lav["nome_lavorazione"]}</div>',
                            unsafe_allow_html=True)
            with cm:
                uph = st.number_input("u", min_value=0.1, step=0.5,
                                      value=float(p.get("uph", uph_def)),
                                      key=f"uph_{i}", label_visibility="collapsed",
                                      help=f"Default: {uph_def} unità/ora")
            with cq:
                qty = st.number_input("q", min_value=0, step=1,
                                      value=int(p.get("qty", 0)),
                                      key=f"qty_{i}", label_visibility="collapsed")
            with ct:
                assigned = st.multiselect("p", options=tutti_nomi,
                                          default=[n for n in p.get("assigned",[]) if n in tutti_nomi],
                                          format_func=lambda n: f"{initials(n)}  {n}",
                                          key=f"team_{i}", label_visibility="collapsed",
                                          placeholder="Assegna persone…")
            with ca:
                st.markdown(avatars_html(assigned, color_map), unsafe_allow_html=True)

            if qty > 0 and assigned:
                job_items.append({"nome": lav["nome_lavorazione"], "uph": float(uph),
                                   "skill": lav["skill_richiesta"],
                                   "quantita": int(qty), "assigned": assigned})

    # Salva preset
    with st.expander("Salva come preset"):
        sc = st.columns([3,1])
        pname = sc[0].text_input("Nome", value=nome_progetto or "",
                                  placeholder="Es. Nike FW25", label_visibility="collapsed")
        if sc[1].button("Salva", use_container_width=True):
            if not pname.strip():
                st.warning("Inserisci un nome")
            elif not job_items:
                st.warning("Nessuna lavorazione compilata")
            else:
                snap = {it["nome"]: {"uph":it["uph"],"qty":it["quantita"],"assigned":it["assigned"]}
                        for it in job_items}
                if _USE_SUPABASE:
                    save_preset_db(pname.strip(), snap)
                else:
                    presets[pname.strip()] = snap; save_presets(presets)
                st.success(f"Preset «{pname.strip()}» salvato")

    # Risultati
    st.divider()
    label = f"Risultati{' — ' + nome_progetto if nome_progetto else ''}"
    st.markdown(f'<div class="sec-hdr" style="font-size:1.3rem">{ICO_FILE} {label}</div>', unsafe_allow_html=True)

    if not job_items:
        st.info("Inserisci almeno una quantità e assegna una persona per vedere la stima.")
    else:
        ore_base_tot = ore_effort_tot = ore_reali_tot = costo_totale = 0.0
        ore_pp: dict[str,float] = {}; costo_pp: dict[str,float] = {}

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

        giorni_reali  = ore_reali_tot / ORE_GIORNATA
        giorni_effort = ore_effort_tot / ORE_GIORNATA
        nomi_c = {n for it in job_items for n in it["assigned"]}
        cap    = df_team[df_team["nome"].isin(nomi_c)]["disponibilita_h_settimana"].sum()
        giorni_cal = (ore_reali_tot / cap * 5) if cap > 0 else None

        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Tempo reale", f"{ore_reali_tot:.1f} h")
        m2.metric("Giorni reali", f"{giorni_reali:.1f}")
        m3.metric("Costo stimato", f"€ {costo_totale:,.0f}")
        if giorni_cal:
            m4.metric("Durata calendario", f"{giorni_cal:.0f} giorni lav.")
        st.caption(f"Effort totale: {ore_effort_tot:.1f} h ({giorni_effort:.1f} gg)")

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

    st.markdown(f'<div class="sec-hdr" style="font-size:0.95rem;font-weight:600;color:#374151">{ICO_WRENCH} Membri del team</div>', unsafe_allow_html=True)

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
        height=60 + 38 * max(len(df_prof), 1),
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
                f'<span style="font-size:11px;color:#888">{ruolo}</span>'
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
