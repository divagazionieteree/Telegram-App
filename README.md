# Bot Telegram Multi-Funzione

Bot Telegram e applicazione terminale con due modalità:
- 📱 **QR Code Generator** - Genera QR code da link
- 📊 **Portafoglio Investimenti** - Analizza e visualizza il tuo portafoglio investimenti con grafici e tabelle

Il progetto include anche script CLI standalone per generare QR code e un'interfaccia terminale interattiva per gestire il portafoglio.

## 📋 Indice

- [Installazione](#-installazione)
- [Utilizzo CLI](#-utilizzo-cli)
  - [QR Code Generator](#qrcode-generator)
  - [Terminale Interattivo Investimenti](#terminale-interattivo-investimenti)
- [Bot Telegram](#-bot-telegram)
  - [Setup](#setup-bot-telegram)
  - [Comandi](#comandi-bot-telegram)
- [Dettagli Investimenti](#-dettagli-investimenti)
  - [Struttura Dati](#struttura-del-file-portafoglio_datajson)
  - [Funzionalità](#funzionalità-investimenti)
  - [Sistema Cache](#sistema-di-cache-locale)
  - [Risoluzione Problemi](#-risoluzione-problemi-investimenti)
- [Zimaboard](#-versione-docker-per-zimaboard)
- [Struttura del Progetto](#-struttura-del-progetto)
- [Requisiti](#-requisiti)

## 🚀 Installazione

### 1. Prerequisiti

Assicurati di avere Python 3.8+ installato.

### 2. Ambiente Virtuale

**Crea un ambiente virtuale (raccomandato):**
```bash
python -m venv venv
```

**Attiva l'ambiente virtuale:**

**Su Linux/Mac:**
```bash
source venv/bin/activate
```

**Su Windows:**
```bash
venv\Scripts\activate
```

### 3. Installa le Dipendenze

```bash
pip install -r requirements.txt
```

**Dipendenze incluse:**
- QR Code: `qrcode`, `Pillow`
- Investimenti: `pandas`, `numpy`, `matplotlib`, `yahooquery`

> **Nota:** Se non installi le dipendenze per investimenti, funzionerà solo la modalità QR code.

### 4. Disattiva l'ambiente virtuale (quando finisci)

```bash
deactivate
```

## 💻 Utilizzo CLI

### QR Code Generator

Genera un QR code da un URL dalla riga di comando.

**Uso Base:**
```bash
python qrcode_generator.py https://www.google.com
```

Questo creerà un file `qrcode.png` nella directory corrente.

**Opzioni Avanzate:**
```bash
# Specificare il nome del file di output
python qrcode_generator.py https://github.com -o mio_qrcode.png

# Personalizzare dimensione e bordo
python qrcode_generator.py https://example.com -s 15 -b 2
```

**Parametri:**
- `url` (obbligatorio): L'URL da codificare nel QR code
- `-o, --output`: Nome del file di output (default: `qrcode.png`)
- `-s, --size`: Dimensione dei box del QR code (default: 10)
- `-b, --border`: Spessore del bordo in box (default: 4)

**Caratteristiche:**
- ✓ Correzione errori ad alto livello (ERROR_CORRECT_H)
- ✓ Output in formato PNG
- ✓ Personalizzazione dimensioni e bordi
- ✓ Interfaccia a riga di comando user-friendly
- ✓ Gestione errori robusta

**Esempi:**
```bash
# QR code per un sito web
python qrcode_generator.py https://www.wikipedia.org

# QR code per un profilo social
python qrcode_generator.py https://twitter.com/username -o twitter_qr.png

# QR code grande con bordo sottile
python qrcode_generator.py https://example.com -s 20 -b 1
```

### Terminale Interattivo Investimenti

Avvia l'applicazione terminale interattiva per gestire il portafoglio:

```bash
python telegram_bot.py
```

**Comandi disponibili:**
- `/metriche` - Mostra metriche principali (valore totale, rendimento, CAGR, costi)
- `/portafoglio` - Mostra tabella dettagliata del portafoglio (come immagine PNG)
- `/grafico_composizione` - Grafico a barre orizzontali della composizione per titolo (percentuali)
- `/grafico_andamento` - Andamento normalizzato dei titoli nel tempo
- `/grafico_geografico` - Distribuzione geografica del portafoglio (barre orizzontali, percentuali)
- `/grafico_tipologia` - Distribuzione per tipologia/settore (barre orizzontali, percentuali)
- `/report_completo` - Genera tutte le visualizzazioni in sequenza
- `/exit` o `/quit` - Esci dall'applicazione

Tutti i grafici e le tabelle vengono salvati nella cartella `output/` con timestamp.

**Prerequisiti:**
- File `portafoglio_data.json` nella directory corrente (vedi [Struttura Dati](#struttura-del-file-portafoglio_datajson))
  - Puoi copiare il file di esempio: `cp portafoglio_data.json.example portafoglio_data.json`
  - Poi modifica `portafoglio_data.json` con i tuoi dati reali
- Connessione Internet per recuperare i prezzi da Yahoo Finance

## 🤖 Bot Telegram

Il progetto include un bot Telegram multi-funzione con due modalità:
- 📱 **QR Code Generator** - Genera QR code da link
- 📊 **Portafoglio Investimenti** - Analizza e visualizza il tuo portafoglio con grafici e tabelle

### Setup Bot Telegram

#### 1. Crea un bot su Telegram

- Apri Telegram e cerca `@BotFather`
- Invia `/newbot` e segui le istruzioni
- Salva il token che ti viene fornito

#### 2. Imposta il token

**Opzione 1 - Variabile d'ambiente (consigliato):**
```bash
export TELEGRAM_BOT_TOKEN='il_tuo_token_qui'
```

**Opzione 2 - File .env (crea un file .env nella root del progetto):**
```
TELEGRAM_BOT_TOKEN=il_tuo_token_qui
```

#### 3. Configura gli ID Telegram autorizzati (opzionale)

Per limitare l'accesso al bot solo a utenti specifici, imposta la variabile d'ambiente:
```bash
export TELEGRAM_ALLOWED_IDS='162087502'
```

**Come ottenere il tuo ID Telegram:**
- Cerca il bot `@userinfobot` su Telegram
- Invia `/start` al bot
- Ti risponderà con il tuo ID (numero)

**Nota:** Se non imposti `TELEGRAM_ALLOWED_IDS`, il bot sarà accessibile a tutti gli utenti.

#### 4. Prepara i dati per investimenti (solo per modalità investimenti)

Crea un file `portafoglio_data.json` nella stessa directory del bot con la struttura dei tuoi investimenti.

**Opzione 1 - Usa il file di esempio:**
```bash
cp portafoglio_data.json.example portafoglio_data.json
# Poi modifica portafoglio_data.json con i tuoi dati reali
```

**Opzione 2 - Crea manualmente:**
Vedi [Struttura Dati](#struttura-del-file-portafoglio_datajson) per dettagli sulla struttura.

#### 5. Avvia il bot

```bash
source venv/bin/activate
python telegram_bot.py
```

### Comandi Bot Telegram

#### Comandi Principali

- `/start` - Avvia il bot e mostra il messaggio di benvenuto (disattiva tutte le modalità)
- `/help` - Mostra la guida completa con tutti i comandi
- `/stop` - Disattiva tutte le modalità attive

#### Modalità QR Code 📱

- `/qrcode` - Attiva la modalità QR code continua
- Dopo `/qrcode`, invia tutti i link che vuoi convertire (uno per volta)

**Esempi:**
```
/qrcode
https://www.google.com
https://github.com
/stop
```

#### Modalità Investimenti 📊

- `/investimenti` - Attiva la modalità investimenti

**Comandi disponibili dopo `/investimenti`:**

**Metriche e Report:**
- `/metriche` - Mostra metriche principali (valore totale, rendimento, CAGR, costi)
- `/portafoglio` - Mostra tabella dettagliata del portafoglio (come immagine)
- `/report_completo` - Invia tutte le visualizzazioni in sequenza

**Grafici:**
- `/grafico_composizione` - Grafico a barre orizzontali della composizione per titolo (percentuali)
- `/grafico_andamento` - Andamento normalizzato dei titoli nel tempo
- `/grafico_geografico` - Distribuzione geografica (barre orizzontali, percentuali)
- `/grafico_tipologia` - Distribuzione per tipologia/settore (barre orizzontali, percentuali)

**Esempi:**
```
/investimenti
/metriche
/portafoglio
/grafico_composizione
/grafico_andamento
/report_completo
/stop
```

### Come Funziona

#### Modalità QR Code

1. **Attiva la modalità:** Invia `/qrcode`
2. **Invia link:** Dopo `/qrcode`, tutti i link che invii verranno automaticamente convertiti in QR code
3. **Disattiva:** Usa `/stop` o un altro comando per uscire dalla modalità

#### Modalità Investimenti

1. **Attiva la modalità:** Invia `/investimenti`
2. **Usa i comandi:** Dopo `/investimenti`, puoi usare tutti i comandi degli investimenti
3. **Grafici e tabelle:** Tutti i risultati vengono inviati come immagini PNG
4. **Dati in tempo reale:** I dati vengono recuperati da Yahoo Finance in tempo reale
5. **Disattiva:** Usa `/stop` per disattivare la modalità

> **Nota:** La modalità investimenti richiede un file `portafoglio_data.json` con i dati del tuo portafoglio.

### Caratteristiche Bot

- ✅ **Due modalità separate** - QR code e investimenti
- ✅ **Autorizzazione utenti** - Controllo accesso tramite ID Telegram
- ✅ **Gestione errori** - Retry automatico e gestione errori di rete
- ✅ **Grafici e tabelle** - Conversione automatica in immagini PNG
- ✅ **Dati in tempo reale** - Recupero prezzi da Yahoo Finance
- ✅ **Compatibilità** - Funziona anche senza dipendenze investimenti (solo QR code)

## 📊 Dettagli Investimenti

### Struttura del File `portafoglio_data.json`

Il file `portafoglio_data.json` contiene i dati del tuo portafoglio.

> **💡 Suggerimento:** È disponibile un file di esempio `portafoglio_data.json.example` nella root del progetto che puoi copiare e personalizzare:
> ```bash
> cp portafoglio_data.json.example portafoglio_data.json
> ```

Ecco la struttura completa:

```json
{
  "nomi_titoli": [
    {
      "nome": "Nome completo dell'ETF",
      "ISIN": "Codice ISIN",
      "TICKER": "SYMBOL.MI",
      "link": "URL al profilo ETF",
      "area_geografica": "Europa",
      "tipologia": "Azione"
    }
  ],
  "operazioni": [
    {
      "data": "YYYY-MM-DD",
      "quote": numero_quote,
      "operazione": "acquisto/vendita",
      "titolo": "SYMBOL.MI"
    }
  ]
}
```

**Campi opzionali per `nomi_titoli`:**
- `area_geografica`: Area geografica del titolo (es. "Europa", "Stati Uniti", "Mondo")
- `tipologia`: Tipologia di investimento (es. "Azione", "Obbligazione", "Commodity")

**Esempio completo:**
```json
{
  "nomi_titoli": [
    {
      "nome": "Amundi MSCI World UCITS ETF Acc",
      "ISIN": "IE000BI8OT95.SG",
      "TICKER": "MWRD.MI",
      "link": "https://www.justetf.com/it/etf-profile.html?isin=IE000BI8OT95",
      "area_geografica": "Mondo",
      "tipologia": "Azione"
    }
  ],
  "operazioni": [
    {
      "data": "2024-01-15",
      "quote": 100,
      "operazione": "acquisto",
      "titolo": "MWRD.MI"
    }
  ]
}
```

#### Aggiungere Nuovi Titoli

1. Apri il file `portafoglio_data.json`
2. Aggiungi un nuovo oggetto nella lista `nomi_titoli`:

```json
{
  "nome": "Nuovo ETF",
  "ISIN": "IE000XXXXXX",
  "TICKER": "NUOVO.MI",
  "link": "https://www.justetf.com/it/etf-profile.html?isin=IE000XXXXXX",
  "area_geografica": "Europa",
  "tipologia": "Azione"
}
```

#### Aggiungere Operazioni

1. Aggiungi un nuovo oggetto nella lista `operazioni`:

```json
{
  "data": "2025-01-15",
  "quote": 100,
  "operazione": "acquisto",
  "titolo": "MWRD.MI"
}
```

**Validazione Automatica:**
- ✅ Controllo formato JSON con messaggi di errore chiari
- ✅ Creazione automatica del file se non esiste (con dati di esempio)
- ✅ Visualizzazione del file direttamente nell'app

> **💡 File di esempio:** Un file `portafoglio_data.json.example` è disponibile nella root del progetto con 6 ETF di esempio e 15 operazioni di esempio. Copialo e personalizzalo con i tuoi dati reali.

### Funzionalità Investimenti

#### Metriche Principali

- **Valore Totale Portafoglio**: Valore attuale calcolato in base ai prezzi di mercato
- **Rendimento Assoluto**: Guadagno/perdita in euro
- **Rendimento Percentuale**: Rendimento percentuale sul valore iniziale
- **CAGR**: Compound Annual Growth Rate (tasso di crescita annuale composto)
- **Investimento Iniziale**: Capitale totale investito
- **Costi Totali**: Somma di tutte le commissioni pagate

#### Grafici Disponibili

1. **Composizione Portafoglio**: Barre orizzontali mostrando la distribuzione percentuale per titolo, ordinata dal maggiore al minore
2. **Andamento Normalizzato**: Grafico lineare mostrando l'andamento di tutti i titoli normalizzato su base 100
3. **Distribuzione Geografica**: Barre orizzontali mostrando la distribuzione percentuale per area geografica, ordinata dal maggiore al minore
4. **Distribuzione per Tipologia**: Barre orizzontali mostrando la distribuzione percentuale per tipologia (Azione, Obbligazione, ecc.), ordinata dal maggiore al minore

#### Report Completo

Il comando `/report_completo` genera in sequenza:
1. Tabella dettagliata del portafoglio
2. Grafico composizione
3. Grafico andamento
4. Grafico geografico
5. Grafico tipologia

### Sistema di Cache Locale

L'applicazione utilizza un sistema di cache locale per ottimizzare le performance:

#### File di Cache
- **Formato**: `cache_mercato_{periodo}_{granularita}.json`
- **Esempio**: `cache_mercato_1y_1d.json`
- **Contenuto**: Dati di mercato con timestamp di creazione

#### Funzionamento
1. **Primo avvio**: Scarica tutti i dati da Yahoo Finance
2. **Avvii successivi**: Carica dalla cache se valida (< 24 ore)
3. **Aggiornamento**: Scarica solo i ticker mancanti
4. **Scadenza**: Cache automaticamente invalidata dopo 24 ore

#### Vantaggi
- ⚡ **Caricamento veloce** (da cache locale)
- 📡 **Meno chiamate API** (riduce sovraccarico Yahoo Finance)
- 🔄 **Aggiornamento intelligente** (solo dati mancanti)
- 💾 **Risparmio banda** (dati salvati localmente)

### Configurazione Parametri

L'applicazione utilizza parametri fissi per semplificare l'uso:

- **Periodo di analisi**: `1y` (1 anno) - configurabile nel codice
- **Granularità dati**: `1d` (giornaliera) - configurabile nel codice

Per modificare questi parametri, edita il file `utils.py` o `investimenti_generator.py`:

```python
PERIODO_DEFAULT = "1y"  # Opzioni: "1y", "2y", "5y", "max"
GRANULARITA_DEFAULT = "1d"  # Opzioni: "1d", "1wk", "1mo"
```

### 🐛 Risoluzione Problemi Investimenti

#### Errore di connessione

- Verifica la connessione internet
- Controlla che Yahoo Finance sia accessibile
- Il bot gestisce automaticamente gli errori di rete e riprova

#### Dati mancanti

- Alcuni ticker potrebbero non essere disponibili su Yahoo Finance
- Verifica che il ticker sia corretto (formato: `SYMBOL.MI` per Borsa Italiana)
- Prova a cambiare il periodo di analisi

#### Performance lente

- Riduci il numero di titoli nel portafoglio
- Usa granularità settimanale o mensile per periodi lunghi
- La cache locale accelera i caricamenti successivi

#### Errori di tipo dati

**Errore**: `TypeError: unsupported operand type(s) for -: 'numpy.ndarray' and 'Timestamp'`
- **Causa**: Incompatibilità tra tipi di indice DataFrame e calcolo differenze date
- **Soluzione**: Il codice gestisce automaticamente queste conversioni

**Errore**: `Cannot compare Timestamp with datetime.date`
- **Causa**: Confronto tra Timestamp e datetime.date
- **Soluzione**: Conversione automatica di tutti i tipi di data in Timestamp

**Errore**: `ArrowInvalid: Could not convert '' with type str: tried to convert to int64`
- **Causa**: Mescolanza di stringhe vuote e numeri nelle colonne del DataFrame
- **Soluzione**: Conversione automatica di tutte le colonne object in string

#### Errori di timezone

**Errore**: `Cannot mix tz-aware with tz-naive values`
- **Causa**: Incompatibilità tra date con e senza timezone da Yahoo Finance
- **Soluzione**: Gestione timezone robusta con controllo individuale di ogni data

## 🐳 Versione Docker per Zimaboard

Per eseguire il bot su Zimaboard in un container Docker, vedi la documentazione nella cartella `telegram_bot_zimaboard/`:

```bash
cd telegram_bot_zimaboard
cat README.md
```

La versione Docker include:
- ✅ Build automatico con Docker Compose
- ✅ Gestione variabili d'ambiente tramite `.env`
- ✅ Volume persistente per i dati del portafoglio
- ✅ Restart automatico in caso di crash
- ✅ Gestione errori di rete avanzata
- ✅ Healthcheck del container

## 📁 Struttura del Progetto

```
QRcode/
├── telegram_bot.py                  # Bot Telegram unificato (QR code + Investimenti)
├── telegram_bot_investimenti.py     # Bot solo investimenti (standalone)
├── qrcode_generator.py              # Modulo per generare QR code
├── investimenti_generator.py        # Generazione metriche, grafici e report investimenti
├── investimenti_streamlit.py        # App Streamlit originale (opzionale)
├── utils.py                         # Modulo utility per investimenti (funzioni core)
├── portafoglio_data.json            # Dati portafoglio (da creare)
├── portafoglio_data.json.example    # File di esempio con 6 ETF e operazioni di esempio
├── requirements.txt                 # Dipendenze Python
├── README.md                        # Questo file
├── output/                          # Cartella per grafici e immagini generate
│   ├── portafoglio_*.png
│   ├── grafico_composizione_*.png
│   ├── grafico_andamento_*.png
│   ├── grafico_geografico_*.png
│   └── grafico_tipologia_*.png
└── telegram_bot_zimaboard/          # Versione Docker per Zimaboard
    ├── telegram_bot.py
    ├── qrcode_generator.py
    ├── investimenti_generator.py
    ├── utils.py
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── env.example
    ├── README.md                    # Documentazione Docker
    └── data/
        └── portafoglio_data.json    # Dati portafoglio (montato come volume)
```

## 📋 Requisiti

### Base (solo QR code)
- Python 3.8+
- `qrcode`, `Pillow`

### Completo (QR code + Investimenti)
- Python 3.8+
- Tutte le dipendenze in `requirements.txt`:
  - `qrcode[pil]`, `Pillow`
  - `pandas`, `numpy`
  - `matplotlib`
  - `yahooquery`
- File `portafoglio_data.json` con i dati del portafoglio
- Connessione Internet per recuperare i prezzi da Yahoo Finance

### Bot Telegram (opzionale)
- Token del bot Telegram (ottienilo da @BotFather)
- (Opzionale) Lista di ID Telegram autorizzati

## 📝 Note

- Il QR code generato può essere letto da qualsiasi lettore di QR code standard (app smartphone, scanner, ecc.)
- La modalità investimenti richiede connessione Internet per recuperare i prezzi da Yahoo Finance
- I grafici e le tabelle vengono generati come immagini PNG
- Il bot gestisce automaticamente gli errori di rete e riprova in caso di problemi
- I dati finanziari sono forniti "così come sono" e non costituiscono consigli di investimento
- Consulta sempre un consulente finanziario per decisioni di investimento

## 🆘 Supporto

Per problemi o suggerimenti:
1. Controlla i log del terminale o del bot
2. Verifica che tutte le dipendenze siano installate correttamente
3. Assicurati di avere una connessione internet stabile
4. Per problemi specifici della versione Docker, consulta `telegram_bot_zimaboard/README.md`

## 📄 Licenza

Questo progetto è per uso personale e didattico.

---

**Nota**: I dati finanziari sono forniti "così come sono" e non costituiscono consigli di investimento. Consulta sempre un consulente finanziario per decisioni di investimento.