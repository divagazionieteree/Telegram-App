# Bot Telegram Multi-Funzione - Docker Version per Zimaboard

Bot Telegram con due modalità:
- 📱 **QR Code Generator** - Genera QR code da link
- 📊 **Portafoglio Investimenti** - Analizza e visualizza il tuo portafoglio investimenti con grafici e tabelle

Configurato per essere eseguito in Docker su Zimaboard.

## 📋 Requisiti

- Docker e Docker Compose installati su Zimaboard
- Token del bot Telegram (ottienilo da @BotFather)
- (Opzionale) Lista di ID Telegram autorizzati
- (Opzionale per Investimenti) File `portafoglio_data.json` con i dati del portafoglio

## 🚀 Installazione su Zimaboard

### 1. Prepara l'ambiente

Copia la cartella `telegram_bot_zimaboard` sulla tua Zimaboard o clona questo repository.

**⚠️ IMPORTANTE:** Assicurati di essere nella directory corretta. Se vedi `docker-compose.yml` e `Dockerfile` con `ls`, sei già nella directory giusta - NON fare `cd telegram_bot_zimaboard`!

### 2. Configura le variabili d'ambiente

Crea un file `.env` nella directory corrente (se sei già in `/DATA/AppData/telegram_bot_zimaboard` non serve fare `cd`):

**Opzione 1 - Usando sudo (SE hai errori "Permission denied"):**

```bash
# Verifica dove sei
pwd
# Dovrebbe essere: /DATA/AppData/telegram_bot_zimaboard

# Verifica i permessi della directory
ls -ld .

# Usa sudo per creare il file
sudo cp env.example .env
sudo chmod 664 .env

# Modifica il file con i tuoi valori usando nano
sudo nano .env
# Oppure usa vi:
# sudo vi .env
```

**Opzione 1b - Senza sudo (se i permessi sono corretti):**
```bash
# Se la directory appartiene a te (casaos), puoi fare:
cp env.example .env
nano .env
```

**Opzione 2 - Se hai problemi di permessi "Permission denied":**

```bash
# Verifica chi è il proprietario della directory
ls -ld .

# Se la directory appartiene a root o altro utente, usa sudo:
sudo cp env.example .env
sudo chmod 664 .env
sudo nano .env

# Oppure cambia il proprietario della directory:
sudo chown -R casaos:casaos /DATA/AppData/telegram_bot_zimaboard
# Poi puoi creare senza sudo:
cp env.example .env
nano .env
```

**Opzione 3 - Creare il file .env con cat (se cp non funziona):**
```bash
# Verifica il contenuto del file esempio
cat env.example

# Crea il file .env usando cat con heredoc:
cat > .env << 'EOF'
# Telegram Bot Token (OBBLIGATORIO)
TELEGRAM_BOT_TOKEN=il_tuo_token_qui

# Telegram Allowed User IDs (OPZIONALE)
TELEGRAM_ALLOWED_IDS=123456789
EOF

# Se anche questo non funziona, usa sudo:
sudo cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=il_tuo_token_qui
TELEGRAM_ALLOWED_IDS=123456789
EOF

# Poi modifica manualmente con nano:
sudo nano .env
```

**Opzione 4 - Usare touch e poi editare:**
```bash
# Crea un file vuoto
touch .env
# Se non funziona:
sudo touch .env

# Modifica con nano
nano .env
# o
sudo nano .env

# Incolla il contenuto di env.example e modifica i valori
```

Modifica il file `.env` con i tuoi valori:

```env
TELEGRAM_BOT_TOKEN=il_tuo_token_qui
TELEGRAM_ALLOWED_IDS=123456789,987654321
```

**Come ottenere il token:**
- Apri Telegram e cerca `@BotFather`
- Invia `/newbot` e segui le istruzioni
- Salva il token che ti viene fornito

**Come ottenere il tuo ID Telegram:**
- Cerca il bot `@userinfobot` su Telegram
- Invia `/start` al bot
- Ti risponderà con il tuo ID (numero)

**Nota:** Se non imposti `TELEGRAM_ALLOWED_IDS`, il bot sarà accessibile a tutti gli utenti.

**🔧 Problemi a creare/modificare il file .env su Zimaboard?**

Se hai errori "Permission denied" quando provi a creare o modificare il file `.env`, prova queste soluzioni in ordine:

1. **Verifica i permessi della directory:**
   ```bash
   # Sei già nella directory corretta? (NON fare cd telegram_bot_zimaboard se sei già dentro!)
   pwd
   # Dovrebbe essere: /DATA/AppData/telegram_bot_zimaboard
   
   # Verifica i permessi
   ls -ld .
   # Verifica il proprietario
   ls -la | head -5
   ```

2. **Usa sudo per creare il file:**
   ```bash
   sudo cp env.example .env
   sudo chmod 664 .env
   sudo nano .env
   ```

3. **Cambia il proprietario della directory (se necessario):**
   ```bash
   # Verifica chi è il proprietario
   ls -ld .
   
   # Cambia il proprietario alla directory completa
   sudo chown -R casaos:casaos /DATA/AppData/telegram_bot_zimaboard
   
   # Ora puoi creare senza sudo:
   cp env.example .env
   nano .env
   ```

4. **Crea il file manualmente con cat:**
   ```bash
   # Mostra il contenuto di esempio
   cat env.example
   
   # Crea il file usando sudo
   sudo tee .env > /dev/null << 'EOF'
   # Telegram Bot Token (OBBLIGATORIO)
   TELEGRAM_BOT_TOKEN=il_tuo_token_qui
   
   # Telegram Allowed User IDs (OPZIONALE)
   TELEGRAM_ALLOWED_IDS=123456789
   EOF
   
   # Modifica i valori con nano
   sudo nano .env
   ```

5. **Modifica direttamente in docker-compose.yml (alternativa):**
   Se non riesci a creare/modificare `.env`, puoi modificare direttamente `docker-compose.yml`:
   ```bash
   sudo nano docker-compose.yml
   # Modifica la sezione environment con i tuoi valori
   ```

### 2.5. Configura dati per investimenti (solo per modalità investimenti)

Se vuoi usare la modalità investimenti, crea un file `portafoglio_data.json` nella directory `./data`:

```bash
mkdir -p data
nano data/portafoglio_data.json
```

Vedi `README_Investimenti.md` nella directory principale del progetto per la struttura completa del file.

**Nota:** Il file viene montato come volume read-only nel container. Se modifichi il file, riavvia il container.

### 3. Build e avvio con Docker Compose

```bash
# Build dell'immagine Docker
# Nota: Il build usa network: host per risolvere problemi DNS durante la compilazione
docker-compose build

# Se hai problemi DNS durante il build, prova:
docker build --network=host --no-cache -t telegram-qrcode-bot .

# Avvia il container
docker-compose up -d

# Visualizza i log
docker-compose logs -f
```

**Nota sul Build:**
- Il build è configurato per usare `network: host` per evitare problemi DNS
- Se il build fallisce per problemi DNS, verifica la connessione Internet di Zimaboard

### 4. Verifica che funzioni

```bash
# Controlla lo stato del container
docker-compose ps

# Visualizza i log in tempo reale
docker-compose logs -f telegram-qrcode-bot
```

Dovresti vedere un messaggio come:
```
🤖 Bot avviato!
🔒 Bot con accesso limitato a X utente/i autorizzato/i
📊 Funzionalità Investimenti: ✅ Disponibile
🤖 Bot Telegram avviato!
📡 Gestione errori di rete attiva - il bot si riconnetterà automaticamente
```

**Nota:** Se vedi errori "NetworkError" nei log, non preoccuparti - il bot gestisce automaticamente questi errori e si riconnette quando la connessione viene ripristinata.

## 📱 Uso del Bot

### Modalità QR Code

1. Apri Telegram e cerca il tuo bot
2. Invia `/start` per iniziare
3. Invia `/qrcode` per attivare la modalità
4. Invia tutti i link che vuoi convertire (uno per volta)
5. Usa `/stop` per disattivare la modalità

### Modalità Investimenti

1. Assicurati di aver configurato `portafoglio_data.json` in `./data/`
2. Invia `/investimenti` per attivare la modalità
3. Usa i comandi per visualizzare metriche, grafici e tabelle
4. Usa `/stop` per disattivare la modalità

### Comandi Disponibili

#### Comandi Principali

- `/start` - Avvia il bot e mostra il messaggio di benvenuto
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
- `/grafico_composizione` - Grafico a torta della composizione per titolo
- `/grafico_andamento` - Andamento normalizzato dei titoli nel tempo
- `/grafico_geografico` - Distribuzione geografica del portafoglio
- `/grafico_tipologia` - Distribuzione per tipologia/settore

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

## 🛠️ Gestione del Container

### Avviare il container

```bash
docker-compose up -d
```

### Fermare il container

```bash
docker-compose stop
```

### Riavviare il container

```bash
docker-compose restart
```

### Fermare e rimuovere il container

```bash
docker-compose down
```

### Visualizzare i log

```bash
# Log in tempo reale
docker-compose logs -f

# Ultime 100 righe
docker-compose logs --tail=100
```

### Aggiornare il bot

```bash
# Ferma il container
docker-compose down

# Ricostruisci l'immagine (se hai modificato il codice)
docker-compose build

# Riavvia
docker-compose up -d
```

### Modificare le configurazioni

Dopo aver modificato il file `.env`:

```bash
docker-compose down
docker-compose up -d
```

## 🔧 Build Manuale (senza Docker Compose)

Se preferisci usare solo Docker:

```bash
# Build dell'immagine
docker build -t telegram-qrcode-bot .

# Esegui il container
docker run -d \
  --name telegram-qrcode-bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN='il_tuo_token' \
  -e TELEGRAM_ALLOWED_IDS='123456789' \
  telegram-qrcode-bot
```

## 🔍 Troubleshooting

### Il bot non risponde

1. **Verifica i log:**
   ```bash
   docker-compose logs telegram-qrcode-bot
   ```

2. **Controlla che il token sia corretto:**
   - Verifica nel file `.env` che `TELEGRAM_BOT_TOKEN` sia impostato correttamente
   - Assicurati che non ci siano spazi extra o caratteri nascosti

3. **Verifica che il container sia in esecuzione:**
   ```bash
   docker-compose ps
   ```

### Errore "Accesso Negato"

Se ricevi il messaggio "Accesso Negato", verifica:
- Che il tuo ID Telegram sia nella lista `TELEGRAM_ALLOWED_IDS` nel file `.env`
- Riavvia il container dopo aver modificato `.env`

### Il container si riavvia continuamente

1. **Controlla i log per errori:**
   ```bash
   docker-compose logs telegram-qrcode-bot
   ```

2. **Verifica che le variabili d'ambiente siano impostate correttamente:**
   ```bash
   docker-compose config
   ```

### Problemi durante il Build (DNS Resolution)

Se durante il `docker compose build` ricevi errori di tipo "Temporary failure resolving 'deb.debian.org'":

**Soluzione 1 - Verifica DNS dell'host:**
```bash
# Verifica che l'host possa risolvere DNS
ping -c 1 8.8.8.8
nslookup deb.debian.org
```

**Soluzione 2 - Build con network host (già configurato):**
Il `docker-compose.yml` è già configurato per usare `network: host` durante il build.

**Soluzione 3 - Build diretto con Docker:**
```bash
docker build --network=host --no-cache -t telegram-qrcode-bot .
```

**Soluzione 4 - Se il problema persiste:**
- Verifica la configurazione DNS di Zimaboard
- Assicurati che Zimaboard abbia accesso a Internet
- Controlla firewall/network settings

### Errori di Rete durante l'Esecuzione

Se vedi errori "NetworkError" o "Temporary failure in name resolution" nei log durante l'esecuzione:

- ✅ **Nessuna azione richiesta**: Il bot gestisce automaticamente questi errori
- Il bot riproverà automaticamente quando la connessione viene ripristinata
- I messaggi in attesa vengono processati automaticamente dopo la riconnessione
- Se il problema persiste per più di alcuni minuti, verifica la connessione Internet di Zimaboard

## 📊 Monitoraggio

Il container include un healthcheck che verifica periodicamente che il processo sia in esecuzione:

```bash
# Verifica lo stato di salute
docker-compose ps
```

## 🔒 Sicurezza

- Il token del bot è gestito tramite variabili d'ambiente
- Il container gira come utente non-root (`botuser`)
- Non esporre il file `.env` pubblicamente
- Usa `TELEGRAM_ALLOWED_IDS` per limitare l'accesso

## 🌐 Configurazione di Rete

Il bot include configurazioni per gestire problemi di rete:

### DNS Configuration
- Il container usa DNS server pubblici (Google DNS e Cloudflare) per garantire risoluzione DNS affidabile
- Configurazione DNS automatica durante il build usando `network: host`
- Configurazione DNS per i container in esecuzione tramite `docker-compose.yml`

### Gestione Errori di Rete
- **Retry automatico**: Il bot riprova automaticamente in caso di errori di connessione temporanei
- **Error handler**: Gestione automatica di `NetworkError`, `RetryAfter`, e `TimeoutError`
- **Riconnessione automatica**: Se la connessione viene persa, il bot si riconnette automaticamente
- **Drop pending updates**: I messaggi accumulati durante disconnessioni vengono ignorati per evitare problemi

### Errori Comuni di Rete

**"Temporary failure in name resolution"**
- Il bot gestisce automaticamente questi errori e riprova
- Se il problema persiste, verifica la connessione di rete di Zimaboard
- Il container usa DNS pubblici come fallback

**"NetworkError" nei log**
- Normalmente gestito automaticamente
- Il bot continuerà a funzionare non appena la connessione viene ripristinata
- Nessuna azione richiesta - il retry è automatico

## 📝 Note

- Il bot usa moduli separati per mantenere il codice modulare:
  - `qrcode_generator.py` - Generazione QR code
  - `investimenti_generator.py` - Generazione metriche, grafici e report investimenti
  - `utils.py` - Funzioni core per investimenti (caricamento dati, calcoli)
- I QR code generati vengono inviati direttamente come immagini, non vengono salvati
- La modalità investimenti richiede un file `portafoglio_data.json` montato come volume
- I grafici e le tabelle vengono generati come immagini PNG e inviati via Telegram
- I dati vengono recuperati in tempo reale da Yahoo Finance
- Il container è configurato per riavviarsi automaticamente in caso di crash (`restart: unless-stopped`)
- Gestione automatica degli errori di rete con retry e riconnessione

## 📊 Struttura File

```
telegram_bot_zimaboard/
├── telegram_bot.py              # Bot Telegram unificato
├── qrcode_generator.py          # Modulo per generare QR code
├── investimenti_generator.py    # Modulo per generare metriche, grafici e report investimenti
├── utils.py                     # Modulo utility per investimenti (funzioni core)
├── requirements.txt             # Dipendenze Python
├── Dockerfile                   # Dockerfile per build immagine
├── docker-compose.yml           # Configurazione Docker Compose
├── .dockerignore                # File da ignorare nel build
├── .env.example                 # File esempio configurazione
├── README.md                    # Questo file
└── data/                        # Directory per dati (montata come volume)
    └── portafoglio_data.json    # File dati portafoglio (opzionale)
```

## 🆘 Supporto

Per problemi o domande, controlla i log del container:
```bash
docker-compose logs -f telegram-qrcode-bot
```

