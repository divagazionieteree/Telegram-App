# Dockerfile per Bot Telegram Multi-Funzione (QR Code + Investimenti)
FROM python:3.11-slim

# Imposta directory di lavoro
WORKDIR /app

# Installa dipendenze di sistema necessarie per Pillow e matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia file requirements
COPY requirements.txt .

# Installa dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia file applicazione
COPY telegram_bot.py .
COPY qrcode_generator.py .
COPY investimenti_generator.py .
COPY utils.py .

# Crea directory per i dati (portafoglio_data.json può essere montato come volume)
RUN mkdir -p /app/data && chmod 755 /app/data

# Crea utente non-root per sicurezza
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Comando di avvio
CMD ["python", "telegram_bot.py"]

