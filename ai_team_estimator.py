"""
AI_Team Estimator v2 — Tool di stima tempi e costi per AI_Team (AI team, Accenture Song).
Legge ai_team_data.xlsx con fogli 'lavorazioni' e 'team'.
Logica derivata dal tariffario reale: ragiona in asset_per_giorno, giornata = 8h.

Run: python3 -m streamlit run ai_team_estimator.py
"""

import os
import streamlit as st
import pandas as pd
from io import BytesIO

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="AI Team Estimator", page_icon="⏱️", layout="wide")

OVERHEAD_DEFAULT = 1.3
ORE_GIORNATA = 8
DEFAULT_XLSX = os.path.join(os.path.dirname(__file__), "ai_team_data.xlsx")


# ============================================================
# LOADER
# ============================================================
@st.cache_data
def load_data(file_bytes: bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes))

    missing = {"lavorazioni", "team"} - set(xls.sheet_names)
    if missing:
        raise ValueError(f"Fogli mancanti: {missing}")

    df_lav = pd.read_excel(xls, sheet_name="lavorazioni")
    req_l = {"tipologia_id", "categoria", "sottocategoria", "nome_lavorazione",
             "variante", "asset_per_giorno", "skill_richiesta"}
    missing_l = req_l - set(df_lav.columns)
    if missing_l:
        raise ValueError(f"Colonne mancanti in 'lavorazioni': {missing_l}")
    df_lav["asset_per_giorno"] = pd.to_numeric(df_lav["asset_per_giorno"], errors="coerce")
    df_lav = df_lav.dropna(subset=["asset_per_giorno"]).reset_index(drop=True)
    df_lav["variante"] = df_lav["variante"].fillna("")

    df_team = pd.read_excel(xls, sheet_name="team")
    req_t = {"id", "nome", "seniority", "costo_orario", "skill_tags", "disponibilita_h_settimana"}
    missing_t = req_t - set(df_team.columns)
    if missing_t:
        raise ValueError(f"Colonne mancanti in 'team': {missing_t}")
    df_team["costo_orario"] = pd.to_numeric(df_team["costo_orario"], errors="coerce")
    df_team["disponibilita_h_settimana"] = pd.to_numeric(df_team["disponibilita_h_settimana"], errors="coerce")
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
    return dict(ore_base=ore_base, ore_tot=ore_tot, md_base=md_base,
                md_tot=md_tot, costo=costo, settimane=settimane)


def skill_gap(job_items, risorse):
    richieste = {it["skill"].lower() for it in job_items if it.get("skill")}
    disponibili = {s for _, r in risorse.iterrows() for s in r["skill_list"]}
    return richieste - disponibili


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⏱️ AI Team\nEstimator")
    st.divider()

    # File
    if os.path.exists(DEFAULT_XLSX):
        with open(DEFAULT_XLSX, "rb") as f:
            file_bytes = f.read()
        st.caption("✅ Dati caricati da `ai_team_data.xlsx`")
        with st.expander("Sostituisci file"):
            up = st.file_uploader("Carica un altro Excel", type=["xlsx"])
            if up:
                file_bytes = up.getvalue()
    else:
        st.warning("File non trovato nella cartella")
        up = st.file_uploader("Carica ai_team_data.xlsx", type=["xlsx"])
        file_bytes = up.getvalue() if up else None

    if not file_bytes:
        st.stop()

    try:
        df_lav, df_team = load_data(file_bytes)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    st.divider()

    # STEP 2 — Team
    st.markdown("**Passo 2 — Chi lavora al job?**")
    has_ruolo = "ruolo" in df_team.columns
    nomi = st.multiselect(
        "Seleziona le persone del team",
        options=df_team["nome"].tolist(),
        format_func=lambda n: (
            f"{n}  ({df_team[df_team['nome']==n]['ruolo'].iloc[0]})"
            if has_ruolo else n
        ),
        placeholder="Scegli una o più persone…",
    )
    risorse = df_team[df_team["nome"].isin(nomi)]

    if not risorse.empty:
        cap = risorse["disponibilita_h_settimana"].sum()
        st.caption(f"Capacità: {cap:.0f} h/settimana · {cap/ORE_GIORNATA:.1f} MD/sett.")

    st.divider()

    # Overhead
    st.markdown("**Parametri avanzati**")
    overhead = st.slider(
        "Overhead",
        1.0, 2.0, OVERHEAD_DEFAULT, 0.05,
        help="Moltiplicatore per riunioni, rework e buffer. 1.3 = +30% sulle ore base."
    )


# ============================================================
# MAIN
# ============================================================
st.header("Passo 1 — Quante lavorazioni hai?")
st.caption(
    "Scrivi il numero di asset nella colonna **Quantità** per ogni tipo di lavorazione del job. "
    "Lascia 0 le righe che non ti servono."
)

# Tabella: solo 3 colonne visibili (gruppo, lavorazione, quantità)
df_edit = df_lav[["sottocategoria", "nome_lavorazione", "variante"]].copy()
df_edit["quantita"] = 0
# Label leggibile: "nome — variante" se c'è variante
df_edit["lavorazione"] = df_lav.apply(
    lambda r: f"{r['nome_lavorazione']}  —  {r['variante']}" if r["variante"] else r["nome_lavorazione"],
    axis=1
)
df_show = df_edit[["sottocategoria", "lavorazione", "quantita"]].copy()

edited = st.data_editor(
    df_show,
    column_config={
        "sottocategoria": st.column_config.TextColumn("Tipo", width="medium"),
        "lavorazione":    st.column_config.TextColumn("Lavorazione", width="large"),
        "quantita":       st.column_config.NumberColumn(
            "Quantità  ✏️",
            min_value=0, step=1, default=0, width="small",
            help="Quanti asset di questo tipo devi produrre?"
        ),
    },
    disabled=["sottocategoria", "lavorazione"],
    hide_index=True,
    use_container_width=True,
    height=72 + 36 * len(df_show),
)

# Costruisci job_items
job_items = []
for i, row in edited.iterrows():
    qty = int(row["quantita"] or 0)
    if qty > 0:
        orig = df_lav.loc[i]
        job_items.append({
            "nome":             orig["nome_lavorazione"],
            "variante":         orig["variante"],
            "asset_per_giorno": float(orig["asset_per_giorno"]),
            "skill":            orig["skill_richiesta"],
            "quantita":         qty,
        })

# ============================================================
# RISULTATI
# ============================================================
st.divider()
st.header("Risultati")

if not job_items:
    st.info("👆 Inserisci almeno una quantità nella tabella sopra per vedere la stima.")
    st.stop()

if risorse.empty:
    st.info("👈 Seleziona almeno una persona del team nella barra laterale.")
    st.stop()

gap = skill_gap(job_items, risorse)
if gap:
    st.warning(f"⚠️ Skill richieste non coperte dal team selezionato: **{', '.join(gap)}**")

res = calcola(job_items, risorse, overhead)

# Metriche principali
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ore totali", f"{res['ore_tot']:.1f} h",
          help=f"Ore base senza overhead: {res['ore_base']:.1f} h")
m2.metric("Giornate (MD)", f"{res['md_tot']:.1f}")
m3.metric("Costo stimato", f"€ {res['costo']:,.0f}")
if res["settimane"]:
    m4.metric("Durata", f"{res['settimane']:.1f} settimane")

st.caption(
    f"Overhead applicato: ×{overhead}  ·  "
    f"ore base {res['ore_base']:.1f} h  →  ore totali {res['ore_tot']:.1f} h  ·  "
    f"1 giornata = {ORE_GIORNATA} h"
)

# Breakdown
with st.expander("Dettaglio per lavorazione"):
    rows = []
    for it in job_items:
        md = it["quantita"] / it["asset_per_giorno"]
        label = f"{it['nome']}  —  {it['variante']}" if it["variante"] else it["nome"]
        rows.append({"Lavorazione": label, "Qta": it["quantita"],
                     "Asset/gg": it["asset_per_giorno"],
                     "MD": round(md, 2), "Ore": round(md * ORE_GIORNATA, 1)})
    rows.append({"Lavorazione": "TOTALE (senza overhead)", "Qta": "",
                 "Asset/gg": "", "MD": round(res["md_base"], 2),
                 "Ore": round(res["ore_base"], 1)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    if not risorse.empty and has_ruolo:
        st.markdown("**Team selezionato**")
        st.dataframe(
            risorse[["nome", "ruolo", "costo_orario", "disponibilita_h_settimana"]].rename(
                columns={"costo_orario": "€/h", "disponibilita_h_settimana": "h/sett"}
            ),
            hide_index=True, use_container_width=True
        )
