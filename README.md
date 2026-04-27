# AI Team Estimator — Guida completa

**Versione:** 1.0  
**Team:** AI_Team, Accenture Song  
**Autore:** Eugenio Bellini

---

## Cos'è e a cosa serve

AI Team Estimator è uno strumento interno per stimare **quanto tempo ci vuole** e **quanto costa** produrre un job creativo con il team AI.

Prima di questo tool, per capire quante ore servivano per un job bisognava farlo a mente o su un foglio Excel manuale. Questo strumento automatizza quel calcolo: basta inserire cosa si deve produrre, quante unità, e chi lavora — il tool calcola tutto il resto in tempo reale.

**Casi d'uso tipici:**
- Stimare un job prima di iniziare la produzione
- Confrontare il costo con budget diversi o team diversi
- Avere un documento formale da allegare all'offerta o al brief interno
- Salvare configurazioni ricorrenti per riusarle in futuro

---

## Come avviare il programma

Il programma gira nel browser. Per avviarlo sul proprio computer:

**Requisiti:** Python 3.10 o superiore installato.

**Installazione dipendenze (una sola volta):**
```
pip install streamlit pandas openpyxl
```

**Avvio:**
```
python3 -m streamlit run ai_team_estimator.py
```

Dopo qualche secondo il browser si apre automaticamente su `http://localhost:8501`.

> Se il browser non si apre, aprirlo manualmente e digitare l'indirizzo sopra.

---

## Struttura dell'interfaccia

L'app è divisa in tre aree principali:

```
┌─────────────────┬──────────────────────────────────────────────────┐
│                 │                                                    │
│    SIDEBAR      │   TAB 1: Costruisci il job                        │
│                 │   TAB 2: Profili team                              │
│  - File Excel   │                                                    │
│  - Overhead     │                                                    │
│  - Lista team   │                                                    │
│                 │                                                    │
└─────────────────┴──────────────────────────────────────────────────┘
```

---

## Il file Excel: ai_team_data.xlsx

Tutto il catalogo lavorazioni e l'anagrafica del team è contenuto in un unico file Excel: `ai_team_data.xlsx`. Il file ha tre fogli:

### Foglio 1 — `lavorazioni`

Contiene il catalogo di tutto ciò che il team può produrre, con i tempi standard.

| Colonna | Significato | Esempio |
|---|---|---|
| `tipologia_id` | Codice identificativo univoco | `GRAFICA-GEN-01` |
| `categoria` | Macrocategoria | `GRAFICA` |
| `sottocategoria` | Gruppo di lavorazione | `GENERAZIONE` |
| `nome_lavorazione` | Nome descrittivo | `Generazione immagine AI` |
| `minuti_per_unita` | Minuti di lavoro per singola unità | `60` |
| `skill_richiesta` | Competenza necessaria | `prompt` |

**Lavorazioni attualmente disponibili:**

| Sottocategoria | Lavorazione | Minuti/unità | Velocità default |
|---|---|---|---|
| GENERAZIONE | Generazione immagine AI | 60 min | 1 unità/ora |
| POST-PRODUZIONE | Post-produzione immagine | 48 min | 1.3 unità/ora |
| COLOR CORRECTION | Color correction foto | 30 min | 2 unità/ora |
| ANIMAZIONE | Animazione frame statico | 90 min | 0.7 unità/ora |
| ANIMAZIONE | Post-produzione animazione | 40 min | 1.5 unità/ora |
| GENERAZIONE | Generazione video AI | 120 min | 0.5 unità/ora |
| POST-PRODUZIONE | Post-produzione video | 60 min | 1 unità/ora |
| COLOR CORRECTION | Color correction video | 45 min | 1.3 unità/ora |

> I valori `minuti_per_unita` possono essere modificati direttamente nell'Excel per adattarli alla velocità reale del team. Dopo ogni modifica all'Excel, ricaricare la pagina del browser.

### Foglio 2 — `team`

Contiene l'anagrafica di tutti i membri del team con i relativi costi.

| Colonna | Significato | Esempio |
|---|---|---|
| `id` | Numero identificativo | `1` |
| `nome` | Nome e cognome completo | `Manuel Ricciardi` |
| `ruolo` | Ruolo nel team | `Senior Graphic Designer` |
| `seniority` | Livello di esperienza | `senior` |
| `costo_orario` | Tariffa in € per ora | `15` |
| `skill_tags` | Competenze separate da virgola | `retouch,compositing,prompt` |
| `disponibilita_h_settimana` | Ore disponibili a settimana | `40` |

**Membri attuali del team:**

| Nome | Ruolo | Seniority | €/ora |
|---|---|---|---|
| Manuel Ricciardi | Senior Graphic Designer | senior | €15/h |
| Alvar S. Rodriguez | Senior Graphic Designer | senior | €15/h |
| Elisa Righi | Senior Graphic Designer | senior | €15/h |
| Andrea Zini | Senior Graphic Designer | senior | €15/h |
| Eugenio Bellini | Junior Graphic Designer | junior | €8/h |
| Giulia Maria Triulzi | Junior Graphic Designer | junior | €8/h |
| Lucia Marina Tomasi | Junior Graphic Designer | junior | €8/h |
| Filippo Audino | Junior Graphic Designer | junior | €8/h |
| Martina Lorini | Junior Graphic Designer | junior | €8/h |
| Anna Zonca | Junior Graphic Designer | junior | €8/h |

### Foglio 3 — `_istruzioni`

Contiene le regole di compilazione dell'Excel. Non viene letto dall'app.

---

## La Sidebar

La sidebar è visibile sempre a sinistra. Contiene tre sezioni.

### 1. File Excel

Al primo avvio il programma carica automaticamente `ai_team_data.xlsx` se si trova nella stessa cartella dello script. Viene mostrata la scritta `ai_team_data.xlsx caricato`.

Se si vuole usare un Excel diverso (es. con lavorazioni di un altro team), espandere la sezione "Sostituisci file" e caricare il nuovo file.

### 2. Buffer overhead ×

Lo slider controlla il moltiplicatore di buffer applicato a tutte le ore calcolate.

**Cos'è l'overhead:** nella realtà, oltre al tempo puro di lavorazione, un job richiede tempo per riunioni, revisioni, aggiustamenti, imprevisti. L'overhead tiene conto di questo margine.

- **Valore 1.0** = nessun buffer (solo ore di puro lavoro)
- **Valore 1.3** = +30% di buffer (default consigliato)
- **Valore 1.5** = +50% (job complessi con molte revisioni)
- **Valore 2.0** = raddoppia le ore (buffer massimo)

### 3. Team

Lista di tutti i membri del team con avatar colorato e ruolo. Gli avatar mostrano le iniziali di nome e cognome. Questa lista si aggiorna automaticamente se si modificano i profili nella tab "Profili team".

---

## TAB 1 — Costruisci il job

Questa è la schermata principale dove si costruisce la stima.

### Passaggio 1 — Nome progetto e preset

**Campo "Nome progetto"** (sinistra): digitare il nome del job che si sta stimando. Esempio: `Nike FW25 — Video Campaign`. Questo nome viene usato nel titolo dei risultati e nel file Excel esportato.

**Dropdown preset** (destra): se in precedenza si è salvato un preset (configurazione di un job simile), selezionarlo qui e cliccare "Carica" per ripristinare tutte le impostazioni in un click.

Il pulsante **X** elimina il preset selezionato.

---

### Passaggio 2 — Lavorazioni

La tabella principale mostra tutte le lavorazioni disponibili, raggruppate per sottocategoria (GENERAZIONE, POST-PRODUZIONE, ecc.).

Per ogni riga ci sono quattro campi da compilare:

#### Colonna "Unità/ora"
Quante unità di quella lavorazione si riescono a produrre in un'ora.

- Viene precompilato con il valore di default dall'Excel (calcolato dai `minuti_per_unita`)
- **Si può modificare** per ogni job: se per un cliente particolare si sa che quella lavorazione è più lenta o più veloce, si cambia il valore
- Esempio: se `Generazione immagine AI` ha default 1 unità/ora ma per questo job si stima 2/ora, si mette 2

> Questo è il campo più importante: permette di personalizzare la velocità per ogni singolo progetto senza toccare l'Excel.

#### Colonna "Quantità"
Quante unità di quella lavorazione servono per il job.

- Default 0 (riga ignorata nel calcolo)
- Esempio: se servono 20 post statici generati con AI, si mette 20 nella riga "Generazione immagine AI"

> Solo le righe con quantità > 0 E almeno una persona assegnata vengono incluse nel calcolo.

#### Colonna "Assegnato a"
Chi lavora su quella specifica lavorazione.

- Cliccare nel campo e selezionare uno o più membri del team dal dropdown
- Gli avatar colorati a destra mostrano le persone selezionate
- Se si assegnano più persone, lavorano **in parallelo**: il tempo si divide per il numero di persone (es. 4 ore con 2 persone = 2 ore reali)

> Assegnare più persone riduce il tempo reale del job, ma non riduce il costo totale (ogni persona viene comunque pagata per le ore che lavora).

---

### Passaggio 3 — Salva come preset

Sezione espandibile in fondo alla tabella lavorazioni.

Dopo aver compilato un job, si può salvare la configurazione completa (unità/ora, quantità, assegnazioni) come preset con un nome a scelta. La prossima volta che si stima un job simile, basta caricare il preset invece di ricompilare tutto da zero.

---

### Passaggio 4 — Risultati

Appare automaticamente sotto le lavorazioni non appena almeno una riga ha quantità > 0 e una persona assegnata.

**Le 4 metriche principali:**

| Metrica | Significato |
|---|---|
| **Tempo reale** | Ore effettive di durata del job (con overhead, divise per le persone in parallelo) |
| **Giorni reali** | Stesso valore in giorni lavorativi da 8 ore |
| **Costo stimato** | Costo totale in € (somma di ore × tariffa per ogni persona) |
| **Durata calendario** | Giorni lavorativi tenendo conto della disponibilità settimanale del team |

Sotto le metriche appare una riga di dettaglio con l'overhead applicato e l'effort totale (somma di tutte le ore di lavoro prima della parallelizzazione).

---

### Come vengono calcolati i numeri

La formula è in tre passaggi:

**Step 1 — Ore base (puro lavoro):**
```
Ore base = Quantità ÷ Unità per ora
```
Esempio: 10 post ÷ 2 unità/ora = 5 ore base

**Step 2 — Ore con overhead (lavoro reale):**
```
Ore con overhead = Ore base × Overhead
```
Esempio: 5 ore × 1.3 = 6.5 ore con overhead

**Step 3 — Ore reali (con parallelismo):**
```
Ore reali = Ore con overhead ÷ Numero di persone assegnate
```
Esempio con 2 persone: 6.5 ore ÷ 2 = 3.25 ore reali di durata del job

**Costo:**
```
Costo = Ore reali × Tariffa oraria (per ogni persona)
```
Esempio: 3.25 ore × €15/h = €48.75 per persona

> Il costo totale è la somma dei costi di tutte le persone su tutte le lavorazioni.

---

### Dettaglio per persona e per lavorazione

Due sezioni espandibili mostrano il breakdown completo:

**Dettaglio per persona:** tabella con ore, giorni e costo individuale per ogni membro del team coinvolto nel job.

**Dettaglio per lavorazione:** tabella con ore base, ore con overhead, giorni reali e persone assegnate per ogni singola lavorazione inclusa nel job.

---

### Export Excel

Il pulsante "Esporta stima in Excel" genera e scarica un file `.xlsx` con tre fogli:

1. **Riepilogo** — dati sintetici del job (nome, data, overhead, ore totali, giorni, costo)
2. **Lavorazioni** — dettaglio di ogni lavorazione con tutti i valori calcolati
3. **Team** — dettaglio per ogni persona (ore, giorni, costo)

Il nome del file generato segue il formato: `stima_NomeProgetto_AAAAMMGG.xlsx`

---

## TAB 2 — Profili team

Questa sezione permette di gestire l'anagrafica del team direttamente dall'app, senza modificare l'Excel.

### La tabella dei membri

Mostra tutti i membri del team in formato editabile. Si può:
- **Modificare** nome, ruolo, seniority, tariffa oraria, skill e disponibilità di qualsiasi membro
- **Aggiungere** un nuovo membro usando la riga vuota in fondo alla tabella
- **Eliminare** una riga selezionandola e premendo il tasto Canc/Delete della tastiera

**Colonne della tabella:**

| Colonna | Contenuto | Come compilare |
|---|---|---|
| **Nome** | Nome e cognome completo | Testo libero |
| **Ruolo** | Posizione nel team | Scegliere dal menu a tendina |
| **Seniority** | Livello di esperienza | junior / mid / senior / lead |
| **€/ora** | Tariffa oraria | Numero intero |
| **Skill** | Competenze specifiche | Parole chiave separate da virgola |
| **H/settimana** | Ore disponibili a settimana | Numero (max 40) |

**Ruoli disponibili:**
- Senior Graphic Designer
- Junior Graphic Designer
- Video Editor
- Art Director
- Motion Designer
- Retoucher
- Altro

**Skill disponibili (esempi):** `retouch`, `compositing`, `lighting`, `prompt`, `video`, `editing`, `color`, `motion`, `3d`, `art direction`

### Anteprima

Sotto la tabella appare una riga di chip colorati con l'iniziale di ogni membro — utile per verificare rapidamente che tutti i nomi siano stati inseriti correttamente.

### Salva profili

Il pulsante verde **"Salva profili"** salva le modifiche in un file locale `profiles.json`. Da quel momento in poi l'app usa questi dati invece di quelli dell'Excel, anche dopo aver riavviato il programma.

> Nota: i profili salvati hanno sempre la priorità sull'Excel. Se si modifica il file `ai_team_data.xlsx` e si vuole che l'app usi i nuovi dati, usare il pulsante "Ripristina da Excel".

### Ripristina da Excel

Cancella `profiles.json` e riporta l'app a leggere i dati direttamente dall'Excel. Utile quando si aggiorna il file Excel con nuove tariffe o nuovi membri.

### Stato attivo

In basso a destra appare un'indicazione dello stato attuale:
- **"Profili personalizzati attivi"** — l'app usa i dati salvati in `profiles.json`
- **"Dati da Excel"** — l'app legge direttamente dall'Excel

---

## File generati dal programma

Oltre all'Excel originale, il programma crea e gestisce due file nella sua cartella:

| File | Contenuto | Quando viene creato |
|---|---|---|
| `profiles.json` | Anagrafica team personalizzata | Quando si clicca "Salva profili" |
| `presets.json` | Configurazioni job salvate | Quando si salva un preset |

Questi file rimangono sul computer anche dopo aver chiuso il browser o il terminale. Si possono eliminare manualmente se si vuole ripartire da zero.

---

## Domande frequenti

**D: Ho modificato l'Excel ma l'app non si aggiorna.**  
R: Streamlit mantiene i dati in cache. Premere il tasto `R` sulla tastiera con il browser aperto sull'app, oppure cliccare il pulsante "Always rerun" in alto a destra. Se non funziona, chiudere e riavviare l'app dal terminale.

**D: La riga non compare nel calcolo.**  
R: Controllare che la riga abbia sia la quantità > 0 sia almeno una persona assegnata nella colonna "Assegnato a". Entrambe le condizioni devono essere soddisfatte.

**D: Ho due persone assegnate ma il tempo si è dimezzato — è giusto?**  
R: Sì, è il comportamento corretto. Se due persone lavorano in parallelo sulla stessa lavorazione, il tempo di durata del job si dimezza. Il costo totale invece rimane uguale (anzi, dipende dalle tariffe individuali di ciascuna persona).

**D: Come faccio ad aggiungere una nuova tipologia di lavorazione?**  
R: Aprire `ai_team_data.xlsx`, andare sul foglio `lavorazioni`, aggiungere una nuova riga rispettando il formato delle colonne (soprattutto `minuti_per_unita` deve essere un numero), salvare e ricaricare l'app.

**D: Posso usarlo per tipi di lavoro diversi dal video/grafica AI?**  
R: Sì. Il tool è completamente parametrico. Si può adattare qualsiasi lista di lavorazioni modificando l'Excel. L'unico vincolo è rispettare i nomi delle colonne.

**D: I costi orari visibili sono quelli reali di fatturazione?**  
R: I valori attuali nell'Excel sono placeholder interni. Verificare con il proprio referente le tariffe ufficiali prima di condividere stime con clienti o stakeholder esterni.

---

## Avvertenze

- I dati del team (nomi, tariffe) sono sensibili. Non condividere screenshot o export con persone esterne al team.
- Prima del deploy su un server condiviso, verificare le policy Accenture sull'hosting di applicazioni interne.
- L'app non ha un sistema di autenticazione nella versione attuale.
