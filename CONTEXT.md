# CONTEXT.md — AI_Team Estimator

## Obiettivo
Web tool interno per l'**AI_Team** di Accenture Song che stima **tempi e costi** di un job leggendo da un unico Excel parametrico (`ai_team_data.xlsx`). Monday non copre questo caso d'uso.

## Stack
- **Streamlit** (Python) — UI form + dashboard
- **pandas** + **openpyxl** — lettura Excel
- File singolo: `ai_team_estimator.py` (~230 righe)
- Deploy target: da decidere (Streamlit Community Cloud è pubblico → per Accenture serve server interno)

## Logica chiave (derivata dal tariffario reale `Tariffario_AI_Video_.csv`)
Il tariffario AI_Team ragiona in **asset al giorno per risorsa**. Giornata standard = **8 ore** (1 MD = 8h).

- `MD per riga = quantità / asset_per_giorno`
- `Ore per riga = MD × 8`
- `Ore totali = Σ ore × overhead` (default 1.3)
- `Costo = (ore_totali / n_risorse) × Σ costo_orario_risorsa`
- `Durata calendar = ore_totali / capacità_settimanale_team`

Validato: 10 post generica (10 asset/gg) + 5 editing base (16 asset/gg) = 10.5h base, 13.65h con overhead 1.3. ✓

## Struttura `ai_team_data.xlsx`

**Foglio `lavorazioni`** → `tipologia_id | categoria | sottocategoria | nome_lavorazione | variante | asset_per_giorno | skill_richiesta`
Convenzione ID: `VID-GS-01` (VIDEO / GENERAZIONE STATICI / 01). Popolato con 9 righe reali del tariffario video.

**Foglio `team`** → `id | nome | ruolo | seniority | costo_orario | skill_tags | disponibilita_h_settimana`
Data validation su seniority (junior/mid/senior/lead). 10 persone reali dell'AI_Team:
- 4 Senior Graphic Designer (€60/h, placeholder): Manuel Ricciardi, Alvar S. Rodriguez, Elisa Righi, Andrea Zini
- 4 Junior Graphic Designer (€30/h, placeholder): Eugenio Bellini, Giulia Maria Triulzi, Lucia Marina Tomasi, Filippo Audino
- 2 Video Editor (€45/h, placeholder): Martina Lorini, Anna Zonca

**Foglio `_istruzioni`** → regole di compilazione e convenzioni.

## Decisioni prese
- Partire con **solo VIDEO**, estendere a STATICI/PDP in futuro. La colonna `categoria` è già pronta.
- **Ore in evidenza** come primo metric (poi MD, costo, settimane).
- **Tariffa oraria per persona** (non costo a MD fisso per seniority).
- **Un solo file Excel** (tre fogli: lavorazioni + team + istruzioni).
- **Giornata = 8h** (coerenza col tariffario reale).
- **Overhead default ×1.3**, slider 1.0–2.0.
- UI con `st.data_editor`: tutte le lavorazioni in tabella, PM mette quantità dove serve.
- Colonna `ruolo` aggiunta al team (Senior GD / Junior GD / Video Editor), mostrata nel multiselect UI.

## Ultimo step completato
- `ai_team_data.xlsx` con 9 righe reali tariffario video + 10 membri reali del team
- `ai_team_estimator.py` con logica asset/giorno, UI data_editor, ore in evidenza
- Logica calcolo testata con scenario verificato a mano
- Naming AI_Team applicato ovunque (era CM1, errore mio)

## Prossimo step
1. Sostituire i **costi orari placeholder** (60/30/45) con le tariffe reali Accenture
2. Verificare **skill_tags per persona**: ora sono uguali per ruolo, ma alcune persone hanno specializzazioni (es. Eugenio fa anche video?). Affinare caso per caso.
3. Verificare seniority Video Editor (ora `mid`, da confermare se junior o senior)
4. Test su un job reale già fatto: confronto stima vs consuntivo
5. Aggiustamenti: overhead per tipologia? Categoria STATICI?

## Roadmap features
1. Export PDF stima
2. Scenario comparison (A vs B, team diversi stesso job)
3. Allocazione intelligente per skill (ora ore distribuite equamente)
4. Storico stime salvate
5. Lettura diretta da SharePoint via Microsoft Graph API

## Punti aperti / rischi
- **Privacy costi**: tariffe interne sono sensibili. V1 mostra tutto. Serve view "solo tempi" separata se va in mano a tutto il team.
- **Policy Accenture hosting**: verificare prima del deploy.
- **Versioning tariffe**: se cambiano a metà anno, serve `valido_da` in `team`.
- **Struttura Excel bloccata**: header fissi, niente celle unite, skill minuscolo/senza spazi.

## Come far girare in locale
```bash
pip install streamlit pandas openpyxl
streamlit run ai_team_estimator.py
```
Apre su `localhost:8501`. Carica `ai_team_data.xlsx` dalla sidebar.
