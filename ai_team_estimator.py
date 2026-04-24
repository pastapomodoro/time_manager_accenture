"""
AI_Team Estimator v2 — Tool di stima tempi e costi per AI_Team (AI team, Accenture Song).
Legge ai_team_data.xlsx con fogli 'lavorazioni' e 'team'.
Logica: asset_per_giorno, 1 MD = 8h.

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

PALETTE = [
    "#7C3AED", "#2563EB", "#059669", "#D97706", "#DC2626",
    "#7C3AED", "#0891B2", "#65A30D", "#C026D3", "#EA580C",
]

st.markdown("""
<style>
.avatar {
    display: inline-flex; align-items: center; justify-content: center;
    width: 30px; height: 30px; border-radius: 50%;
    color: white; font-size: 11px; font-weight: 700;
    margin-right: 3px; flex-shrink: 0;
}
.avatar-row { display: flex; flex-wrap: wrap; align-items: center; gap: 2px; margin-top: 4px; }
.task-label { font-weight: 600; font-size: 15px; }
.task-sub { color: #888; font-size: 12px; margin-bottom: 2px; }
.section-header {
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: #888; margin: 18px 0 6px 0;
}
</style>
""", unsafe_allow_html=True)


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
# HELPERS
# ============================================================
def initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()


def avatar_html(name: str, color: str) -> str:
    return f'<span class="avatar" style="background:{color}">{initials(name)}</span>'


def avatars_html(names, color_map) -> str:
    if not names:
        return '<span style="color:#aaa;font-size:13px;">nessuno assegnato</span>'
    return '<div class="avatar-row">' + "".join(avatar_html(n, color_map[n]) for n in names) + "</div>"


# ============================================================
# SIDEBAR — file + overhead
# ============================================================
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
        st.warning("File non trovato — carica manualmente")
        up = st.file_uploader("ai_team_data.xlsx", type=["xlsx"])
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
    overhead = st.slider("Overhead ×", 1.0, 2.0, OVERHEAD_DEFAULT, 0.05,
                         help="1.3 = +30% per riunioni e rework")

    # Legenda persone nella sidebar
    st.divider()
    st.markdown("**Team**")
    color_map = {row["nome"]: PALETTE[i % len(PALETTE)] for i, row in df_team.iterrows()}
    has_ruolo = "ruolo" in df_team.columns
    for _, row in df_team.iterrows():
        col_av, col_info = st.columns([1, 4])
        with col_av:
            st.markdown(avatar_html(row["nome"], color_map[row["nome"]]), unsafe_allow_html=True)
        with col_info:
            ruolo = row["ruolo"] if has_ruolo else row["seniority"]
            st.caption(f"**{row['nome'].split()[0]}**  \n{ruolo}")


# ============================================================
# MAIN — una riga per lavorazione
# ============================================================
st.header("Stima job")
st.caption("Per ogni lavorazione: inserisci la **quantità** e assegna le **persone** che ci lavorano.")

tutti_nomi = df_team["nome"].tolist()
job_items = []

# Raggruppa per sottocategoria
gruppi = df_lav.groupby("sottocategoria", sort=False)

for gruppo_nome, gruppo_df in gruppi:
    st.markdown(f'<div class="section-header">{gruppo_nome}</div>', unsafe_allow_html=True)

    for i, lav_row in gruppo_df.iterrows():
        label = lav_row["nome_lavorazione"]
        if lav_row["variante"]:
            label += f"  —  {lav_row['variante']}"

        col_name, col_qty, col_team, col_av = st.columns([3, 1, 3, 2])

        with col_name:
            st.markdown(f'<div class="task-label">{label}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="task-sub">{lav_row["asset_per_giorno"]:.0f} asset/giorno</div>',
                        unsafe_allow_html=True)

        with col_qty:
            qty = st.number_input(
                "Qta", min_value=0, step=1, value=0,
                key=f"qty_{i}", label_visibility="collapsed"
            )

        with col_team:
            assigned = st.multiselect(
                "Assegna a",
                options=tutti_nomi,
                format_func=lambda n: f"{initials(n)}  {n}",
                key=f"team_{i}",
                label_visibility="collapsed",
                placeholder="Assegna persone…",
            )

        with col_av:
            st.markdown(avatars_html(assigned, color_map), unsafe_allow_html=True)

        if qty > 0 and assigned:
            job_items.append({
                "nome":             lav_row["nome_lavorazione"],
                "variante":         lav_row["variante"],
                "asset_per_giorno": float(lav_row["asset_per_giorno"]),
                "skill":            lav_row["skill_richiesta"],
                "quantita":         int(qty),
                "assigned":         assigned,
            })

    st.divider()


# ============================================================
# RISULTATI
# ============================================================
if not job_items:
    st.info("Inserisci almeno una quantità e assegna una persona per vedere la stima.")
    st.stop()

# Calcolo con assegnazione per task
ore_totali = 0.0
costo_totale = 0.0
md_base_totale = 0.0
ore_per_persona: dict[str, float] = {}
costo_per_persona: dict[str, float] = {}

for it in job_items:
    md = it["quantita"] / it["asset_per_giorno"]
    ore = md * ORE_GIORNATA * overhead
    n = len(it["assigned"])
    ore_pp = ore / n
    md_base_totale += md
    ore_totali += ore
    for nome in it["assigned"]:
        tariffa = df_team.loc[df_team["nome"] == nome, "costo_orario"].iloc[0]
        ore_per_persona[nome] = ore_per_persona.get(nome, 0) + ore_pp
        costo_per_persona[nome] = costo_per_persona.get(nome, 0) + ore_pp * tariffa
        costo_totale += ore_pp * tariffa

# Durata: ore totali / capacità team assegnato
nomi_coinvolti = {n for it in job_items for n in it["assigned"]}
cap_sett = df_team[df_team["nome"].isin(nomi_coinvolti)]["disponibilita_h_settimana"].sum()
settimane = ore_totali / cap_sett if cap_sett > 0 else None

st.subheader("Risultati")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ore totali", f"{ore_totali:.1f} h",
          help=f"Ore base (senza overhead): {md_base_totale * ORE_GIORNATA:.1f} h")
m2.metric("Giornate (MD)", f"{ore_totali / ORE_GIORNATA:.1f}")
m3.metric("Costo stimato", f"€ {costo_totale:,.0f}")
if settimane:
    m4.metric("Durata", f"{settimane:.1f} settimane")

st.caption(f"Overhead ×{overhead}  ·  1 giornata = {ORE_GIORNATA} h")

with st.expander("Dettaglio per persona"):
    rows_p = []
    for nome in sorted(ore_per_persona):
        tariffa = df_team.loc[df_team["nome"] == nome, "costo_orario"].iloc[0]
        ruolo = df_team.loc[df_team["nome"] == nome, "ruolo"].iloc[0] if has_ruolo else ""
        rows_p.append({
            "": avatar_html(nome, color_map[nome]),
            "Nome": nome,
            "Ruolo": ruolo,
            "Ore": round(ore_per_persona[nome], 1),
            "Costo": f"€ {costo_per_persona[nome]:,.0f}",
        })
    df_p = pd.DataFrame(rows_p)
    st.dataframe(
        df_p[["Nome", "Ruolo", "Ore", "Costo"]],
        hide_index=True, use_container_width=True
    )

with st.expander("Dettaglio per lavorazione"):
    rows_l = []
    for it in job_items:
        md = it["quantita"] / it["asset_per_giorno"]
        label = f"{it['nome']}  —  {it['variante']}" if it["variante"] else it["nome"]
        rows_l.append({
            "Lavorazione": label,
            "Qta": it["quantita"],
            "Asset/gg": it["asset_per_giorno"],
            "MD": round(md, 2),
            "Ore (con overhead)": round(md * ORE_GIORNATA * overhead, 1),
            "Assegnato a": ", ".join(it["assigned"]),
        })
    st.dataframe(pd.DataFrame(rows_l), hide_index=True, use_container_width=True)
