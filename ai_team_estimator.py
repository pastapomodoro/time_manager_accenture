"""
AI_Team Estimator v2 — Tool di stima tempi e costi per AI_Team (AI team, Accenture Song).
Legge ai_team_data.xlsx con fogli 'lavorazioni' e 'team'.
Logica derivata dal tariffario reale: ragiona in asset_per_giorno, giornata = 8h.

Run: streamlit run ai_team_estimator.py
"""

import os
import streamlit as st
import pandas as pd
from io import BytesIO

from streamlit_theme import inject_theme

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="AI Team Estimator", layout="wide")
inject_theme()

OVERHEAD_DEFAULT = 1.3
ORE_GIORNATA = 8  # standard tariffario (1 MD = 8 ore)
DEFAULT_XLSX = os.path.join(os.path.dirname(__file__), "ai_team_data.xlsx")


# ============================================================
# LOADER
# ============================================================
@st.cache_data
def load_data(file_bytes: bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes))

    required_sheets = {"lavorazioni", "team"}
    missing = required_sheets - set(xls.sheet_names)
    if missing:
        raise ValueError(f"Fogli mancanti: {missing}. Trovati: {xls.sheet_names}")

    df_lav = pd.read_excel(xls, sheet_name="lavorazioni")
    req_l = {"tipologia_id", "categoria", "sottocategoria", "nome_lavorazione",
             "variante", "asset_per_giorno", "skill_richiesta"}
    missing_l = req_l - set(df_lav.columns)
    if missing_l:
        raise ValueError(f"Colonne mancanti nel foglio 'lavorazioni': {missing_l}")
    df_lav["asset_per_giorno"] = pd.to_numeric(df_lav["asset_per_giorno"], errors="coerce")
    df_lav = df_lav.dropna(subset=["asset_per_giorno"]).reset_index(drop=True)
    df_lav["variante"] = df_lav["variante"].fillna("")

    df_team = pd.read_excel(xls, sheet_name="team")
    req_t = {"id", "nome", "seniority", "costo_orario", "skill_tags", "disponibilita_h_settimana"}
    missing_t = req_t - set(df_team.columns)
    if missing_t:
        raise ValueError(f"Colonne mancanti nel foglio 'team': {missing_t}")
    df_team["costo_orario"] = pd.to_numeric(df_team["costo_orario"], errors="coerce")
    df_team["disponibilita_h_settimana"] = pd.to_numeric(
        df_team["disponibilita_h_settimana"], errors="coerce"
    )
    df_team["skill_list"] = df_team["skill_tags"].fillna("").apply(
        lambda s: [t.strip().lower() for t in str(s).split(",") if t.strip()]
    )
    df_team = df_team.dropna(subset=["costo_orario"]).reset_index(drop=True)

    return df_lav, df_team


# ============================================================
# LOGICA
# ============================================================
def calcola(job_items, risorse, overhead):
    md_base = sum(it["quantita"] / it["asset_per_giorno"] for it in job_items)
    ore_base = md_base * ORE_GIORNATA
    ore_tot = ore_base * overhead
    md_tot = ore_tot / ORE_GIORNATA

    n = max(len(risorse), 1)
    ore_per_risorsa = ore_tot / n
    costo = sum(ore_per_risorsa * row["costo_orario"] for _, row in risorse.iterrows())

    capacita_sett = risorse["disponibilita_h_settimana"].sum()
    settimane = ore_tot / capacita_sett if capacita_sett > 0 else None

    return {
        "ore_base": ore_base,
        "ore_tot": ore_tot,
        "md_base": md_base,
        "md_tot": md_tot,
        "costo": costo,
        "settimane": settimane,
    }


def skill_gap(job_items, risorse):
    richieste = {it["skill"].lower() for it in job_items if it.get("skill")}
    disponibili = set()
    for _, row in risorse.iterrows():
        disponibili.update(row["skill_list"])
    return richieste - disponibili


# ============================================================
# UI
# ============================================================
st.title("AI Team Estimator")
st.caption("Stima tempi e costi — tariffario AI_Team (asset/giorno, 8 h/MD).")

with st.sidebar:
    st.header("Dati")

    # Auto-load se il file è nella stessa cartella
    if os.path.exists(DEFAULT_XLSX):
        st.success("`ai_team_data.xlsx` caricato automaticamente.")
        with st.expander("Usa un file diverso"):
            file_data = st.file_uploader("Sostituisci ai_team_data.xlsx", type=["xlsx"])
        if file_data is None:
            with open(DEFAULT_XLSX, "rb") as f:
                file_bytes = f.read()
        else:
            file_bytes = file_data.getvalue()
    else:
        st.info("File non trovato nella cartella — carica manualmente")
        file_data = st.file_uploader("ai_team_data.xlsx", type=["xlsx"])
        file_bytes = file_data.getvalue() if file_data else None

    st.divider()
    st.header("Parametri")
    overhead = st.slider(
        "Overhead (riunioni, rework, buffer)",
        1.0, 2.0, OVERHEAD_DEFAULT, 0.05,
        help="1.3 = +30% sulle ore base"
    )

if file_bytes is None:
    st.info("Carica **ai_team_data.xlsx** dalla barra laterale per iniziare.")
    st.stop()

try:
    df_lav, df_team = load_data(file_bytes)
except ValueError as e:
    st.error(str(e))
    st.stop()

# Layout: job a sinistra, team a destra
col_job, col_team = st.columns([3, 2])

with col_job:
    st.subheader("Job da stimare")
    st.caption("Imposta la quantità solo per le lavorazioni necessarie; lascia 0 le altre.")

    _base = df_lav[
        [
            "tipologia_id",
            "categoria",
            "sottocategoria",
            "nome_lavorazione",
            "variante",
            "asset_per_giorno",
        ]
    ].copy()
    _base["quantita"] = 0
    # Quantità subito dopo nome lavorazione: tutta la tabella visibile in altezza, niente taglio a 500px
    df_edit = _base[
        [
            "tipologia_id",
            "nome_lavorazione",
            "quantita",
            "categoria",
            "sottocategoria",
            "variante",
            "asset_per_giorno",
        ]
    ]

    _n = len(df_edit)
    _editor_height = int(72 + 38 * _n)

    edited = st.data_editor(
        df_edit,
        column_config={
            "tipologia_id": st.column_config.TextColumn("ID", width="small"),
            "nome_lavorazione": st.column_config.TextColumn(
                "Lavorazione", width="large"
            ),
            "quantita": st.column_config.NumberColumn(
                "Quantità",
                min_value=0,
                step=1,
                default=0,
                width="small",
                help="Quantità da stimare per questa riga",
            ),
            "categoria": st.column_config.TextColumn("Cat.", width="small"),
            "sottocategoria": st.column_config.TextColumn(
                "Sottocategoria", width="medium"
            ),
            "variante": st.column_config.TextColumn("Variante", width="medium"),
            "asset_per_giorno": st.column_config.NumberColumn(
                "Asset/gg", width="small", format="%d"
            ),
        },
        disabled=[
            "tipologia_id",
            "nome_lavorazione",
            "categoria",
            "sottocategoria",
            "variante",
            "asset_per_giorno",
        ],
        hide_index=True,
        use_container_width=True,
        height=_editor_height,
    )

    # Costruisci job_items usando l'indice numerico (immune a tipologia_id non univoci)
    job_items = []
    for i, row in edited.iterrows():
        qty = int(row["quantita"] or 0)
        if qty > 0:
            orig = df_lav.loc[i]
            job_items.append({
                "tipologia_id":    orig["tipologia_id"],
                "nome":            orig["nome_lavorazione"],
                "variante":        orig["variante"],
                "asset_per_giorno": float(orig["asset_per_giorno"]),
                "skill":           orig["skill_richiesta"],
                "quantita":        qty,
            })

with col_team:
    st.subheader("Team")
    st.caption("Seleziona le risorse assegnate al job.")

    has_ruolo = "ruolo" in df_team.columns
    nomi = st.multiselect(
        "Risorse",
        options=df_team["nome"].tolist(),
        format_func=lambda n: (
            f"{n} — {df_team[df_team['nome'] == n]['ruolo'].iloc[0]}"
            if has_ruolo else
            f"{n} ({df_team[df_team['nome'] == n]['seniority'].iloc[0]})"
        )
    )
    risorse = df_team[df_team["nome"].isin(nomi)]

    if not risorse.empty:
        cols_show = ["nome"]
        if has_ruolo:
            cols_show.append("ruolo")
        cols_show += ["seniority", "costo_orario", "skill_tags"]
        st.dataframe(risorse[cols_show], hide_index=True, use_container_width=True)
        cap = risorse["disponibilita_h_settimana"].sum()
        st.caption(f"Capacità team: **{cap:.0f} h/settimana** ({cap / ORE_GIORNATA:.1f} MD/settimana)")

st.divider()

if not job_items:
    st.warning("Metti almeno una quantità > 0 nella tabella delle lavorazioni")
    st.stop()

if risorse.empty:
    st.warning("Seleziona almeno una risorsa")
    st.stop()

gap = skill_gap(job_items, risorse)
if gap:
    st.warning(f"Skill richieste ma non coperte dal team: **{', '.join(gap)}**")

res = calcola(job_items, risorse, overhead)

st.subheader("Stima")
m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Ore totali",
    f"{res['ore_tot']:.1f} h",
    f"×{overhead} overhead",
    help=f"Ore base (senza overhead): {res['ore_base']:.1f} h"
)
m2.metric("MD (giornate)", f"{res['md_tot']:.2f}")
m3.metric("Costo", f"€ {res['costo']:,.0f}")
if res["settimane"]:
    m4.metric("Durata calendar", f"{res['settimane']:.1f} sett.")

with st.expander("Breakdown per lavorazione"):
    df_break = pd.DataFrame([
        {
            "Lavorazione": f"{it['nome']} — {it['variante']}" if it["variante"] else it["nome"],
            "Qta": it["quantita"],
            "Asset/gg": it["asset_per_giorno"],
            "MD": round(it["quantita"] / it["asset_per_giorno"], 3),
            "Ore": round((it["quantita"] / it["asset_per_giorno"]) * ORE_GIORNATA, 2),
        }
        for it in job_items
    ])
    totale = {
        "Lavorazione": "— TOTALE (senza overhead) —",
        "Qta": "",
        "Asset/gg": "",
        "MD": round(res["md_base"], 3),
        "Ore": round(res["ore_base"], 2),
    }
    df_break = pd.concat([df_break, pd.DataFrame([totale])], ignore_index=True)
    st.dataframe(df_break, hide_index=True, use_container_width=True)
    st.caption(
        f"Con overhead ×{overhead}: **{res['ore_tot']:.1f} h** ({res['md_tot']:.2f} MD). "
        f"Una giornata = {ORE_GIORNATA} h."
    )
