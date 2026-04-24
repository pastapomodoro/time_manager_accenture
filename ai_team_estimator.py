"""
AI_Team Estimator — stima tempi e costi per AI_Team, Accenture Song.
Logica: minuti per unità (editabile per progetto), 8h/giorno lavorativo.

Run: python3 -m streamlit run ai_team_estimator.py
"""

import os
import streamlit as st
import pandas as pd
from io import BytesIO

# ── CONFIG ────────────────────────────────────────────────────
st.set_page_config(page_title="AI Team Estimator", page_icon="⏱️", layout="wide")

OVERHEAD_DEFAULT = 1.3
ORE_GIORNATA = 8.0          # ore per giornata lavorativa
MINUTI_GIORNATA = ORE_GIORNATA * 60
DEFAULT_XLSX = os.path.join(os.path.dirname(__file__), "ai_team_data.xlsx")

PALETTE = ["#7C3AED","#2563EB","#059669","#D97706","#DC2626",
           "#0891B2","#65A30D","#C026D3","#EA580C","#0F766E"]

st.markdown("""
<style>
.avatar {
    display:inline-flex; align-items:center; justify-content:center;
    width:30px; height:30px; border-radius:50%;
    color:white; font-size:11px; font-weight:700; margin-right:3px;
}
.avatar-row { display:flex; flex-wrap:wrap; align-items:center; gap:2px; margin-top:2px; }
.task-name  { font-weight:600; font-size:15px; line-height:1.3; }
.task-sub   { color:#888; font-size:12px; }
.group-hdr  {
    font-size:12px; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:#888; margin:20px 0 4px 0;
}
</style>
""", unsafe_allow_html=True)


# ── LOADER ────────────────────────────────────────────────────
@st.cache_data
def load_data(file_bytes: bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes))
    missing = {"lavorazioni", "team"} - set(xls.sheet_names)
    if missing:
        raise ValueError(f"Fogli mancanti: {missing}")

    df_lav = pd.read_excel(xls, sheet_name="lavorazioni")
    req = {"tipologia_id", "sottocategoria", "nome_lavorazione", "minuti_per_unita", "skill_richiesta"}
    miss = req - set(df_lav.columns)
    if miss:
        raise ValueError(f"Colonne mancanti in 'lavorazioni': {miss}")
    df_lav["minuti_per_unita"] = pd.to_numeric(df_lav["minuti_per_unita"], errors="coerce")
    df_lav = df_lav.dropna(subset=["minuti_per_unita"]).reset_index(drop=True)

    df_team = pd.read_excel(xls, sheet_name="team")
    req_t = {"id","nome","seniority","costo_orario","skill_tags","disponibilita_h_settimana"}
    miss_t = req_t - set(df_team.columns)
    if miss_t:
        raise ValueError(f"Colonne mancanti in 'team': {miss_t}")
    df_team["costo_orario"] = pd.to_numeric(df_team["costo_orario"], errors="coerce")
    df_team["disponibilita_h_settimana"] = pd.to_numeric(df_team["disponibilita_h_settimana"], errors="coerce")
    df_team = df_team.dropna(subset=["costo_orario"]).reset_index(drop=True)
    return df_lav, df_team


# ── HELPERS ───────────────────────────────────────────────────
def initials(name: str) -> str:
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

def avatar_html(name: str, color: str) -> str:
    return f'<span class="avatar" style="background:{color}">{initials(name)}</span>'

def avatars_html(names, color_map) -> str:
    if not names:
        return '<span style="color:#bbb;font-size:13px;">—</span>'
    return '<div class="avatar-row">' + "".join(avatar_html(n, color_map[n]) for n in names) + "</div>"


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.title("⏱️ AI Team\nEstimator")
    st.divider()

    if os.path.exists(DEFAULT_XLSX):
        with open(DEFAULT_XLSX, "rb") as f:
            file_bytes = f.read()
        st.caption("✅ `ai_team_data.xlsx` caricato")
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
        df_lav, df_team = load_data(file_bytes)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    st.divider()
    overhead = st.slider(
        "Overhead ×", 1.0, 2.0, OVERHEAD_DEFAULT, 0.05,
        help="Moltiplicatore per riunioni, rework, buffer. 1.3 = +30%."
    )

    st.divider()
    st.markdown("**Team**")
    color_map = {row["nome"]: PALETTE[i % len(PALETTE)] for i, row in df_team.iterrows()}
    has_ruolo = "ruolo" in df_team.columns
    for _, row in df_team.iterrows():
        c1, c2 = st.columns([1, 5])
        c1.markdown(avatar_html(row["nome"], color_map[row["nome"]]), unsafe_allow_html=True)
        c2.caption(f"**{row['nome'].split()[0]}**  \n{row['ruolo'] if has_ruolo else row['seniority']}")


# ── MAIN ──────────────────────────────────────────────────────
st.header("Costruisci il job")
st.caption(
    "Per ogni lavorazione: imposta **quante unità riesci a fare in 1 ora** "
    "(cambia il default se per questo progetto sei più veloce o più lento), "
    "la **quantità** totale di asset e le **persone** assegnate."
)

tutti_nomi = df_team["nome"].tolist()
job_items = []

# Intestazioni colonne
hcols = st.columns([3, 1.2, 1, 3, 1.8])
for col, label in zip(hcols, ["Lavorazione", "Unità/ora", "Quantità", "Assegnato a", ""]):
    col.markdown(f"<span style='font-size:12px;font-weight:700;color:#888'>{label}</span>",
                 unsafe_allow_html=True)
st.markdown("<hr style='margin:4px 0 8px 0'>", unsafe_allow_html=True)

gruppi = df_lav.groupby("sottocategoria", sort=False)

for gruppo_nome, gruppo_df in gruppi:
    st.markdown(f'<div class="group-hdr">{gruppo_nome}</div>', unsafe_allow_html=True)

    for i, lav in gruppo_df.iterrows():
        c_name, c_min, c_qty, c_team, c_av = st.columns([3, 1.2, 1, 3, 1.8])

        with c_name:
            st.markdown(f'<div class="task-name">{lav["nome_lavorazione"]}</div>', unsafe_allow_html=True)

        with c_min:
            # Converti minuti_per_unita → unità/ora per il display
            default_uph = round(60 / lav["minuti_per_unita"], 1)
            uph = st.number_input(
                "uph", min_value=0.1, step=0.5,
                value=float(default_uph),
                key=f"min_{i}", label_visibility="collapsed",
                help=f"Default dal tariffario: {default_uph} unità/ora. Cambialo se per questo progetto vai più veloce o lento."
            )

        with c_qty:
            qty = st.number_input(
                "qta", min_value=0, step=1, value=0,
                key=f"qty_{i}", label_visibility="collapsed"
            )

        with c_team:
            assigned = st.multiselect(
                "persone", options=tutti_nomi,
                format_func=lambda n: f"{initials(n)}  {n}",
                key=f"team_{i}", label_visibility="collapsed",
                placeholder="Assegna persone…",
            )

        with c_av:
            st.markdown(avatars_html(assigned, color_map), unsafe_allow_html=True)

        if qty > 0 and assigned:
            job_items.append({
                "nome":     lav["nome_lavorazione"],
                "uph":      float(uph),   # unità per ora
                "skill":    lav["skill_richiesta"],
                "quantita": int(qty),
                "assigned": assigned,
            })


# ── RISULTATI ─────────────────────────────────────────────────
st.divider()
st.header("Risultati")

if not job_items:
    st.info("Inserisci almeno una quantità e assegna una persona per vedere la stima.")
    st.stop()

# Calcolo
ore_base_tot  = 0.0
ore_effort_tot = 0.0   # effort totale (somma ore × persone, usato per costo)
ore_reali_tot  = 0.0   # tempo reale (ore ÷ n persone in parallelo per ogni task)
ore_pp: dict[str, float]   = {}
costo_pp: dict[str, float] = {}
costo_totale = 0.0

for it in job_items:
    ore_base   = it["quantita"] / it["uph"]
    ore_con_oh = ore_base * overhead
    n          = len(it["assigned"])
    ore_reali  = ore_con_oh / n              # con n persone in parallelo

    ore_base_tot   += ore_base
    ore_effort_tot += ore_con_oh
    ore_reali_tot  += ore_reali

    for nome in it["assigned"]:
        tariffa = float(df_team.loc[df_team["nome"] == nome, "costo_orario"].iloc[0])
        ore_pp[nome]   = ore_pp.get(nome, 0)   + ore_reali
        costo_pp[nome] = costo_pp.get(nome, 0) + ore_reali * tariffa
        costo_totale  += ore_reali * tariffa

giorni_reali  = ore_reali_tot  / ORE_GIORNATA
giorni_effort = ore_effort_tot / ORE_GIORNATA

# Durata calendar: capacità team coinvolto (giorni lavorativi)
nomi_coinvolti = {n for it in job_items for n in it["assigned"]}
cap_h_sett     = df_team[df_team["nome"].isin(nomi_coinvolti)]["disponibilita_h_settimana"].sum()
giorni_cal     = (ore_tot_tot / cap_h_sett * 5) if cap_h_sett > 0 else None  # giorni lun-ven

# Metriche
m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Tempo reale",
    f"{ore_reali_tot:.1f} h",
    help=f"Ore effettive considerando le persone che lavorano in parallelo. Senza overhead: {ore_base_tot:.1f} h"
)
m2.metric(
    "Giorni reali",
    f"{giorni_reali:.1f}",
    help=f"Giorni lavorativi effettivi (tempo reale ÷ {ORE_GIORNATA:.0f}h)"
)
m3.metric(
    "Costo stimato",
    f"€ {costo_totale:,.0f}",
    help=f"Basato sul tempo reale × tariffa oraria di ogni persona"
)
if giorni_cal:
    m4.metric(
        "Durata calendario",
        f"{giorni_cal:.0f} giorni lav.",
        help="Giorni lun-ven considerando la disponibilità del team selezionato"
    )

st.caption(
    f"Overhead ×{overhead}  ·  1 giornata = {ORE_GIORNATA:.0f} h  ·  "
    f"Effort totale: {ore_effort_tot:.1f} h ({giorni_effort:.1f} giorni)"
)

# Breakdown per persona
with st.expander("Dettaglio per persona"):
    rows_p = []
    for nome in sorted(ore_pp):
        tariffa = float(df_team.loc[df_team["nome"] == nome, "costo_orario"].iloc[0])
        ruolo   = df_team.loc[df_team["nome"] == nome, "ruolo"].iloc[0] if has_ruolo else ""
        rows_p.append({
            "Nome":    nome,
            "Ruolo":   ruolo,
            "Ore":     round(ore_pp[nome], 1),
            "Giorni":  round(ore_pp[nome] / ORE_GIORNATA, 1),
            "Costo":   f"€ {costo_pp[nome]:,.0f}",
        })
    st.dataframe(pd.DataFrame(rows_p), hide_index=True, use_container_width=True)

# Breakdown per lavorazione
with st.expander("Dettaglio per lavorazione"):
    rows_l = []
    for it in job_items:
        ore_b = it["quantita"] / it["uph"]
        ore_c = ore_b * overhead
        rows_l.append({
            "Lavorazione":    it["nome"],
            "Qta":            it["quantita"],
            "Unità/ora":      it["uph"],
            "Ore (base)":     round(ore_b, 1),
            "Ore (overhead)": round(ore_c, 1),
            "Giorni":         round(ore_c / ORE_GIORNATA, 1),
            "Assegnato a":    ", ".join(it["assigned"]),
        })
    st.dataframe(pd.DataFrame(rows_l), hide_index=True, use_container_width=True)
