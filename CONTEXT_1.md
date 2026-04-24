# CONTEXT.md — CM1 Estimator

## Obiettivo
Web tool interno per il **team CM1** — team AI di Accenture Song — che stima **tempi e costi** di un job leggendo due Excel parametrici:
- `tempistiche.xlsx` → tabella conversione "tipologia lavorazione → minuti per unità"
- `risorse.xlsx` → anagrafica team (seniority, costo orario, skill, disponibilità)

L'utente seleziona tipologie di lavorazione + quantità + team → il tool calcola ore totali, costo, durata stimata.

Monday non copre questo caso d'uso (stima parametrica da tabelle modificabili).

## Stack
- **Streamlit** (Python) — UI form + dashboard, gira in locale o su server interno
- **pandas** + **openpyxl** — lettura Excel
- File singolo: `cm1_estimator.py` (~250 righe)
- Deploy target: da decidere (Streamlit Community Cloud è pubblico → per Accenture serve server interno o PC condiviso)

## Struttura Excel (assunzioni da validare con Excel reali)

### `tempistiche.xlsx` — foglio `lavorazioni`
| tipologia_id | nome_lavorazione | minuti_per_unita | skill_richiesta |
|---|---|---|---|

### `risorse.xlsx` — foglio `team`
| id | nome | seniority | costo_orario | skill_tags | disponibilita_h_settimana |
|---|---|---|---|---|---|

`skill_tags` = stringa con skill separate da virgola (es. `retouch,lighting`)

## Ultimo step completato
Scheletro Streamlit funzionante (`cm1_estimator.py`) con:
- Upload dei 2 Excel dalla sidebar + validazione colonne
- Multiselect tipologie con quantità per ciascuna
- Multiselect team
- Calcolo: ore base, ore con overhead (×1.3 default), costo totale, durata in settimane/giorni
- Warning skill mancanti
- Breakdown dettagliato espandibile
- Cache Streamlit sugli Excel (`@st.cache_data`)

## Prossimo step
1. **Testare con 2 Excel reali** (anche dummy ma nel formato definitivo del team CM1) → aggiustare parsing se le colonne differiscono dalle assunzioni
2. **Allocazione intelligente per skill**: attualmente le ore sono divise equamente tra risorse. Serve logica che assegni ogni task alla risorsa con skill matching + regola di priorità (seniority? costo più basso? disponibilità?)
3. **Export PDF della stima** per condivisione PM/client

## Decisioni chiave prese
- **Niente database**: Excel = source of truth. Chi gestisce tariffe/tempistiche aggiorna Excel, non impara un tool nuovo.
- **Upload manuale** dei 2 Excel come v1. Upgrade futuro a Microsoft Graph API (lettura diretta da SharePoint) solo se l'aggiornamento frequente diventa un collo di bottiglia → richiede app registration Azure AD via IT Accenture.
- **Costo calcolato, mai salvato**: `ore × tariffa`. Mai persistere il valore computato (diventa incoerente al cambio tariffa).
- **Ore lavorative/giorno = 7.5** (costante in cima al file, da validare con standard Accenture)
- **Overhead default ×1.3** (riunioni, rework, buffer) — slider configurabile 1.0–2.0
- **Scope v1 deliberatamente ristretto**: niente allocazione per skill, niente dipendenze tra task, niente scenario comparison, niente storico. Aggiungere solo dopo validazione uso reale.

## Punti aperti / rischi
- **Privacy costi**: tariffe orarie interne Accenture sono dato sensibile. Se il tool viene usato da tutto il team (non solo PM/lead), serve una view "solo tempi" separata da "tempi + costi". Attualmente tutti vedono tutto.
- **Policy Accenture su AI/hosting**: da verificare prima del deploy — dove possono vivere i dati (tariffe + nomi persone + progetti clienti).
- **Struttura Excel da bloccare**: prima riga header fissa, ID univoci mai basati sul nome, un foglio per tabella, niente celle unite.
- **Versioning tariffe**: se le tariffe cambiano il 1° del mese, un job stimato il 30 quale tariffa usa? Potrebbe servire campo `valido_da` in `risorse.xlsx`.

## Come far girare in locale
```bash
pip install streamlit pandas openpyxl
streamlit run cm1_estimator.py
```
Si apre su `localhost:8501`.
