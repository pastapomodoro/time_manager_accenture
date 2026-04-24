"""
CM1 Estimator — stima tempi e costi da Excel parametrici (tempistiche + risorse).
"""
from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

# Costanti (validare con standard Accenture)
ORE_LAVORATIVE_GIORNO = 7.5
OVERHEAD_DEFAULT = 1.3

# Colonne attese
COL_LAVORAZIONI = [
    "tipologia_id",
    "nome_lavorazione",
    "minuti_per_unita",
    "skill_richiesta",
]
COL_TEAM = [
    "id",
    "nome",
    "seniority",
    "costo_orario",
    "skill_tags",
    "disponibilita_h_settimana",
]

FOG_LAVORAZIONI = "lavorazioni"
FOG_TEAM = "team"


@st.cache_data
def _load_lavorazioni(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=FOG_LAVORAZIONI)


@st.cache_data
def _load_team(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=FOG_TEAM)


def _validate_columns(df: pd.DataFrame, expected: list[str], label: str) -> list[str]:
    missing = [c for c in expected if c not in df.columns]
    if missing:
        return [f"{label}: colonne mancanti {missing}. Presenti: {list(df.columns)}"]
    return []


def _parse_skill_tags(s: Any) -> set[str]:
    if pd.isna(s) or s is None:
        return set()
    return {t.strip().lower() for t in str(s).split(",") if t.strip()}


def _skill_match(richiesta: str, resource_tags: set[str]) -> bool:
    r = (richiesta or "").strip().lower()
    if not r:
        return True
    return r in resource_tags or any(r in t or t in r for t in resource_tags if t)


def main() -> None:
    st.set_page_config(page_title="CM1 Estimator", layout="wide")
    st.title("CM1 Estimator")
    st.caption("Stima tempi e costi da `tempistiche.xlsx` e `risorse.xlsx`.")

    with st.sidebar:
        st.subheader("File Excel")
        f_temp = st.file_uploader("tempistiche.xlsx (foglio `lavorazioni`)", type=["xlsx"])
        f_ris = st.file_uploader("risorse.xlsx (foglio `team`)", type=["xlsx"])
        overhead = st.slider(
            "Fattore overhead (riunioni, buffer)",
            min_value=1.0,
            max_value=2.0,
            value=OVERHEAD_DEFAULT,
            step=0.05,
        )
        st.caption(
            f"Ore lavorative/giorno: {ORE_LAVORATIVE_GIORNO} · Overhead: ×{overhead}"
        )

    if not f_temp or not f_ris:
        st.info("Carica entrambi gli Excel dalla sidebar per iniziare.")
        st.stop()

    t_bytes = f_temp.getvalue()
    r_bytes = f_ris.getvalue()

    try:
        df_t = _load_lavorazioni(t_bytes)
        df_r = _load_team(r_bytes)
    except Exception as e:
        st.error(f"Errore lettura Excel: {e}")
        st.stop()

    err_t = _validate_columns(df_t, COL_LAVORAZIONI, "tempistiche")
    err_r = _validate_columns(df_r, COL_TEAM, "risorse")
    if err_t or err_r:
        for e in err_t + err_r:
            st.error(e)
        st.stop()

    df_t = df_t.copy()
    df_t["__key__"] = df_t["tipologia_id"].astype(str) + " — " + df_t[
        "nome_lavorazione"
    ].astype(str)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Lavorazioni e quantità")
        ids = df_t["__key__"].tolist()
        selected = st.multiselect("Tipologie", options=ids, default=ids[:1] if ids else [])

    qty_map: dict[str, float] = {}
    for key in selected:
        row = df_t[df_t["__key__"] == key].iloc[0]
        tid = str(row["tipologia_id"])
        with col1:
            qty_map[tid] = float(
                st.number_input(
                    f"Quantità — {row['nome_lavorazione']}",
                    min_value=0.0,
                    value=1.0,
                    step=1.0,
                    key=f"q_{key}",
                )
            )

    with col2:
        st.subheader("Team")
        df_r = df_r.copy()
        team_labels = [
            f"{r['id']} — {r['nome']} ({r['seniority']})"
            for _, r in df_r.iterrows()
        ]
        df_r["__label__"] = team_labels
        pick = st.multiselect(
            "Risorse",
            options=df_r["__label__"].tolist(),
            default=df_r["__label__"].tolist()[:1] if len(df_r) else [],
        )

    if not selected or not pick:
        st.warning("Seleziona almeno una tipologia e almeno una risorsa.")
        st.stop()

    team_sel = df_r[df_r["__label__"].isin(pick)]
    n_res = max(len(team_sel), 1)

    rows_breakdown: list[dict[str, Any]] = []
    minuti_base_totali = 0.0
    warnings_skill: list[str] = []

    for key in selected:
        row = df_t[df_t["__key__"] == key].iloc[0]
        tid = str(row["tipologia_id"])
        q = qty_map.get(tid, 0.0)
        mpu = float(row["minuti_per_unita"])
        minuti_riga = mpu * q
        minuti_base_totali += minuti_riga
        skill_req = str(row["skill_richiesta"]) if pd.notna(row["skill_richiesta"]) else ""

        for _, tr in team_sel.iterrows():
            tags = _parse_skill_tags(tr["skill_tags"])
            if skill_req and not _skill_match(skill_req, tags):
                warnings_skill.append(
                    f"`{tr['nome']}` potrebbe non coprire la skill `{skill_req}` "
                    f"per `{row['nome_lavorazione']}`"
                )

        # v1: ore divise equamente tra risorse selezionate
        minuti_per_risorsa = minuti_riga / n_res
        for _, tr in team_sel.iterrows():
            ore = minuti_per_risorsa / 60.0
            costo = ore * float(tr["costo_orario"])
            rows_breakdown.append(
                {
                    "tipologia": row["nome_lavorazione"],
                    "risorsa": tr["nome"],
                    "minuti": minuti_per_risorsa,
                    "ore": ore,
                    "costo": costo,
                }
            )

    ore_base = minuti_base_totali / 60.0
    ore_con_overhead = ore_base * overhead

    if warnings_skill:
        st.warning("Skill: controlla le assegnazioni (v1 divide le ore in modo equo).\n" + "\n".join(
            f"- {w}" for w in sorted(set(warnings_skill))
        ))

    st.subheader("Riepilogo")
    costo_base = sum(r["costo"] for r in rows_breakdown)
    costo_tot = costo_base * overhead

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ore base (lavoro)", f"{ore_base:.2f} h")
    c2.metric(f"Ore con overhead ×{overhead}", f"{ore_con_overhead:.2f} h")
    c3.metric("Costo stimato (ore × tariffa, con overhead)", f"€ {costo_tot:,.2f}")
    h_sett = team_sel["disponibilita_h_settimana"].replace(0, pd.NA).dropna()
    cap_sett = float(h_sett.sum()) if len(h_sett) else 0.0
    if cap_sett > 0:
        sett = ore_con_overhead / cap_sett
        giorni = ore_con_overhead / ORE_LAVORATIVE_GIORNO
    else:
        sett = giorni = float("inf")
    c4.metric(
        "Durata (indicativa)",
        f"{sett:.1f} sett."
        if cap_sett and sett != float("inf")
        else "n/d",
    )
    if cap_sett > 0 and sett != float("inf"):
        st.caption(
            f"Giorni lavorativi indicativi (÷{ORE_LAVORATIVE_GIORNO} h/g): ~{giorni:.1f}"
        )
    else:
        st.caption("Durata: somma `disponibilita_h_settimana` nelle risorse = 0 o assente.")

    with st.expander("Breakdown dettagliato", expanded=True):
        if rows_breakdown:
            bd = pd.DataFrame(rows_breakdown)
            # applica overhead alle ore mostrate
            bd["ore_con_overhead"] = bd["ore"] * overhead
            bd["costo_con_overhead"] = bd["costo"] * overhead
            st.dataframe(
                bd[
                    [
                        "tipologia",
                        "risorsa",
                        "minuti",
                        "ore",
                        "ore_con_overhead",
                        "costo",
                        "costo_con_overhead",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.write("Nessun dato.")


if __name__ == "__main__":
    main()
