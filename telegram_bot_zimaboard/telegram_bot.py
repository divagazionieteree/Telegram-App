#!/usr/bin/env python3
"""
Bot Telegram per generare QR code da link e analizzare portafoglio investimenti.
Versione Docker per Zimaboard.
"""

import os
import logging
import io
import asyncio
import json
import sys
from datetime import datetime, timedelta, date
from telegram import Update
from telegram.error import NetworkError, RetryAfter, TimedOut
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from qrcode_generator import genera_qrcode
import re

# Importa funzioni per investimenti (gestione importazione condizionale)
try:
    from investimenti_generator import (
        genera_metriche_portafoglio,
        genera_tabella_portafoglio,
        genera_grafico_composizione,
        genera_grafico_andamento,
        genera_grafico_geografico,
        genera_grafico_tipologia,
        INVESTIMENTI_AVAILABLE as INV_AVAILABLE,
        KALEIDO_AVAILABLE,
        MATPLOTLIB_AVAILABLE,
        PERIODO_DEFAULT,
        GRANULARITA_DEFAULT
    )
except ImportError:
    # Se il modulo non è disponibile, usa valori di default
    INV_AVAILABLE = False
    KALEIDO_AVAILABLE = False
    MATPLOTLIB_AVAILABLE = False
    PERIODO_DEFAULT = "1y"
    GRANULARITA_DEFAULT = "1d"

# Importa funzioni per investimenti
# Nota: Streamlit è stato rimosso da utils.py - non è più necessario il mock
try:
    import pandas as pd
    import numpy as np
    from yahooquery import Ticker
    from collections import defaultdict
    from PIL import Image
    
    # Importa funzioni da utils.py
    from utils import (
        carica_dati_portafoglio,
        recupera_dati_mercato,
        calcola_portafoglio_operazioni_tabella,
        calcola_distribuzione_portafoglio
    )
    
    # Usa le configurazioni importate da investimenti_generator
    INVESTIMENTI_AVAILABLE = INV_AVAILABLE
except ImportError as e:
    # Se le dipendenze non sono disponibili
    if 'INV_AVAILABLE' in globals():
        INVESTIMENTI_AVAILABLE = INV_AVAILABLE
    else:
        INVESTIMENTI_AVAILABLE = False
    logging.warning(f"⚠️ Funzionalità investimenti non disponibili: {e}")

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token del bot Telegram (da variabile d'ambiente - OBBLIGATORIO)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Lista ID Telegram autorizzati
# Formato: separati da virgola (es. "123456789,987654321")
# Oppure lascia vuoto per disabilitare il controllo
ALLOWED_USER_IDS = os.getenv('TELEGRAM_ALLOWED_IDS', '').strip()
if ALLOWED_USER_IDS:
    ALLOWED_USER_IDS = [int(uid.strip()) for uid in ALLOWED_USER_IDS.split(',') if uid.strip().isdigit()]
else:
    ALLOWED_USER_IDS = []  # Lista vuota = nessuna restrizione


def is_authorized(user_id: int) -> bool:
    """
    Verifica se l'utente è autorizzato ad usare il bot.
    
    Args:
        user_id (int): ID Telegram dell'utente
    
    Returns:
        bool: True se autorizzato, False altrimenti
    """
    if not ALLOWED_USER_IDS:  # Lista vuota = nessuna restrizione
        return True
    return user_id in ALLOWED_USER_IDS


async def check_authorization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Verifica l'autorizzazione e invia un messaggio se non autorizzato.
    
    Returns:
        bool: True se autorizzato, False altrimenti
    """
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        logger.warning(f"Tentativo di accesso non autorizzato da ID: {user_id}")
        await update.message.reply_text(
            "⛔ Accesso Negato\n\n"
            "Non sei autorizzato ad utilizzare questo bot.\n"
            "Contatta l'amministratore per ottenere l'accesso."
        )
        return False
    return True


def is_valid_url(text):
    """Verifica se il testo è un URL valido."""
    url_pattern = re.compile(
        r'^https?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...o IP
        r'(?::\d+)?'  # porta opzionale
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(text) is not None


async def genera_e_invia_qrcode(update: Update, url: str):
    """
    Helper function per generare e inviare un QR code.
    Usa la funzione genera_qrcode da qrcode_generator.py
    """
    try:
        # Mostra messaggio di attesa
        wait_message = await update.message.reply_text("⏳ Sto generando il QR code...")
        
        # Genera il QR code in memoria usando la funzione da qrcode_generator.py
        qr_bytes = genera_qrcode(
            url=url,
            dimensione=10,
            bordo=4,
            return_bytes=True
        )
        
        # Invia l'immagine del QR code
        await update.message.reply_photo(
            photo=qr_bytes,
            caption=f"✅ QR code generato!\n🔗 Link: {url}"
        )
        
        # Elimina il messaggio di attesa
        await wait_message.delete()
        
        logger.info(f"QR code generato per: {url}")
        
    except Exception as e:
        logger.error(f"Errore: {e}")
        await update.message.reply_text(
            f"❌ Errore durante la generazione del QR code: {str(e)}"
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start."""
    # Verifica autorizzazione
    if not await check_authorization(update, context):
        return
    
    # Disattiva le modalità se attive
    context.user_data['qrcode_mode'] = False
    context.user_data['investimenti_mode'] = False
    
    welcome_message = (
        "👋 Ciao! Sono un bot multi-funzione.\n\n"
        "📤 Modalità disponibili:\n"
        "• /qrcode - Genera QR code da link\n"
    )
    
    if INVESTIMENTI_AVAILABLE:
        welcome_message += "• /investimenti - Analizza portafoglio investimenti\n"
    
    welcome_message += (
        "\n💡 Esempi:\n"
        "• /qrcode → poi invia link\n"
    )
    
    if INVESTIMENTI_AVAILABLE:
        welcome_message += "• /investimenti → poi usa i comandi (es. /metriche)\n"
    
    welcome_message += "\nUsa /help per maggiori informazioni!"
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /help."""
    # Verifica autorizzazione
    if not await check_authorization(update, context):
        return
    
    # Disattiva le modalità se attive
    context.user_data['qrcode_mode'] = False
    context.user_data['investimenti_mode'] = False
    
    # Costruisci il messaggio di help senza formattazione Markdown complessa
    help_text = (
        "ℹ️ Come usare il bot:\n\n"
        "✅ Comandi principali:\n"
        "/start - Avvia il bot\n"
        "/help - Mostra questo messaggio\n"
        "/qrcode - Attiva modalità QR code\n"
        "/stop - Disattiva modalità attive\n\n"
    )
    
    if INVESTIMENTI_AVAILABLE:
        help_text += (
            "📊 Modalità Investimenti:\n"
            "1. Invia /investimenti per attivare\n"
            "2. Poi usa i comandi:\n"
            "   • /metriche - Metriche principali\n"
            "   • /portafoglio - Tabella portafoglio\n"
            "   • /grafico_composizione - Grafico composizione\n"
            "   • /grafico_andamento - Andamento titoli\n"
            "   • /grafico_geografico - Distribuzione geografica\n"
            "   • /grafico_tipologia - Distribuzione tipologia\n"
            "   • /report_completo - Report completo\n\n"
        )
    
    help_text += (
        "📤 Modalità QR Code:\n"
        "1. Invia /qrcode per attivare\n"
        "2. Poi invia tutti i link che vuoi convertire\n"
        "3. I link verranno processati automaticamente\n\n"
        "💡 Usa /stop per disattivare qualsiasi modalità"
    )
    
    await update.message.reply_text(help_text)


async def qrcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /qrcode - attiva la modalità continua."""
    # Verifica autorizzazione
    if not await check_authorization(update, context):
        return
    
    # Disattiva investimenti e attiva QR code
    context.user_data['investimenti_mode'] = False
    context.user_data['qrcode_mode'] = True
    
    message = (
        "✅ Modalità QR code attivata!\n\n"
        "📤 Ora puoi inviare tutti i link che vuoi convertire.\n"
        "Ogni link verrà automaticamente convertito in QR code.\n\n"
        "💡 Invia un link per iniziare, oppure /stop per disattivare."
    )
    await update.message.reply_text(message)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce gli errori che possono verificarsi durante l'esecuzione del bot."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    if isinstance(context.error, NetworkError):
        logger.warning(f"Network error: {context.error}")
    elif isinstance(context.error, RetryAfter):
        logger.warning(f"Rate limit: {context.error}")
        await asyncio.sleep(context.error.retry_after)
    elif isinstance(context.error, TimedOut):
        logger.warning(f"Timeout error: {context.error}")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /stop - disattiva le modalità attive."""
    # Verifica autorizzazione
    if not await check_authorization(update, context):
        return
    
    # Disattiva tutte le modalità
    qrcode_active = context.user_data.get('qrcode_mode', False)
    investimenti_active = context.user_data.get('investimenti_mode', False)
    
    context.user_data['qrcode_mode'] = False
    context.user_data['investimenti_mode'] = False
    
    message = "🛑 Modalità disattivate:\n"
    if qrcode_active:
        message += "• QR code\n"
    if investimenti_active:
        message += "• Investimenti\n"
    
    if not qrcode_active and not investimenti_active:
        message = "ℹ️ Nessuna modalità attiva."
    
    await update.message.reply_text(message)


async def investimenti_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /investimenti - attiva la modalità investimenti."""
    if not await check_authorization(update, context):
        return
    
    if not INVESTIMENTI_AVAILABLE:
        await update.message.reply_text(
            "❌ Funzionalità investimenti non disponibile.\n"
            "Installa le dipendenze necessarie: pip install matplotlib pandas numpy yahooquery"
        )
        return
    
    # Disattiva modalità QR code e attiva investimenti
    context.user_data['qrcode_mode'] = False
    context.user_data['investimenti_mode'] = True
    
    message = (
        "✅ Modalità Investimenti attivata!\n\n"
        "📊 Comandi disponibili:\n"
        "• /metriche - Metriche principali\n"
        "• /portafoglio - Tabella portafoglio\n"
        "• /grafico_composizione - Grafico composizione\n"
        "• /grafico_andamento - Andamento titoli\n"
        "• /grafico_geografico - Distribuzione geografica\n"
        "• /grafico_tipologia - Distribuzione tipologia\n"
        "• /report_completo - Report completo\n\n"
        "💡 Usa /stop per disattivare la modalità."
    )
    await update.message.reply_text(message)


# ===== FUNZIONI HELPER PER INVESTIMENTI =====

async def genera_e_invia_immagine(update: Update, img_bytes: bytes, caption: str = ""):
    """Helper per inviare immagini"""
    try:
        await update.message.reply_photo(
            photo=img_bytes,
            caption=caption
        )
    except Exception as e:
        logger.error(f"Errore nell'invio dell'immagine: {e}")
        await update.message.reply_text(f"❌ Errore nell'invio dell'immagine: {str(e)}")


# ===== COMANDI INVESTIMENTI =====

async def comando_metriche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /metriche - Mostra le metriche principali"""
    if not await check_authorization(update, context):
        return
    
    # Verifica modalità investimenti
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text(
            "⚠️ Modalità Investimenti non attiva.\n\n"
            "Usa /investimenti per attivarla, oppure /help per informazioni."
        )
        return
    
    await update.message.reply_text("⏳ Sto calcolando le metriche...")
    
    try:
        nomi_titoli, operazioni = carica_dati_portafoglio()
        if not nomi_titoli or not operazioni:
            await update.message.reply_text("❌ Impossibile caricare i dati del portafoglio!")
            return
        
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        report = calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi)
        
        if report.empty or len(report) == 0:
            await update.message.reply_text("❌ Nessun dato disponibile per il calcolo.")
            return
        
        # Usa la funzione da investimenti_generator
        messaggio = genera_metriche_portafoglio(report)
        await update.message.reply_text(messaggio)
        
    except Exception as e:
        logger.error(f"Errore in comando_metriche: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def comando_portafoglio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /portafoglio - Mostra tabella portafoglio"""
    if not await check_authorization(update, context):
        return
    
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    await update.message.reply_text("⏳ Sto preparando la tabella del portafoglio...")
    
    try:
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        report = calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi)
        
        if report.empty:
            await update.message.reply_text("❌ Nessun dato disponibile.")
            return
        
        # Usa la funzione da investimenti_generator
        img_bytes = genera_tabella_portafoglio(report)
        await genera_e_invia_immagine(update, img_bytes, "📊 *Tabella Portafoglio*")
        
    except Exception as e:
        logger.error(f"Errore in comando_portafoglio: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def comando_grafico_composizione(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /grafico_composizione"""
    if not await check_authorization(update, context):
        return
    
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    await update.message.reply_text("⏳ Sto generando il grafico...")
    
    try:
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        report = calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi)
        
        if report.empty:
            await update.message.reply_text("❌ Nessun dato disponibile.")
            return
        
        # Usa la funzione da investimenti_generator
        img_bytes = genera_grafico_composizione(report)
        await genera_e_invia_immagine(update, img_bytes, "🥧 *Composizione Portafoglio*")
        
    except Exception as e:
        logger.error(f"Errore in comando_grafico_composizione: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def comando_grafico_andamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /grafico_andamento"""
    if not await check_authorization(update, context):
        return
    
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    await update.message.reply_text("⏳ Sto generando il grafico di andamento...\n⏱️ Questo può richiedere alcuni secondi.")
    
    try:
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        
        # Usa la funzione da investimenti_generator
        img_bytes = genera_grafico_andamento(prezzi_dict, mappa_nomi)
        await genera_e_invia_immagine(update, img_bytes, "📈 *Andamento Titoli*")
        
    except Exception as e:
        logger.error(f"Errore in comando_grafico_andamento: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def comando_grafico_geografico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /grafico_geografico"""
    if not await check_authorization(update, context):
        return
    
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    await update.message.reply_text("⏳ Sto generando il grafico geografico...")
    
    try:
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        
        try:
            # Usa la funzione da investimenti_generator
            img_bytes = genera_grafico_geografico(nomi_titoli, operazioni, prezzi_dict)
            await genera_e_invia_immagine(update, img_bytes, "🌍 *Distribuzione Geografica*")
        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
        
    except Exception as e:
        logger.error(f"Errore in comando_grafico_geografico: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def comando_grafico_tipologia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /grafico_tipologia"""
    if not await check_authorization(update, context):
        return
    
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    await update.message.reply_text("⏳ Sto generando il grafico per tipologia...")
    
    try:
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        
        try:
            # Usa la funzione da investimenti_generator
            img_bytes = genera_grafico_tipologia(nomi_titoli, operazioni, prezzi_dict)
            await genera_e_invia_immagine(update, img_bytes, "📊 *Distribuzione per Tipologia*")
        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
        
    except Exception as e:
        logger.error(f"Errore in comando_grafico_tipologia: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def comando_report_completo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /report_completo"""
    if not await check_authorization(update, context):
        return
    
    if not context.user_data.get('investimenti_mode', False):
        await update.message.reply_text("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    await update.message.reply_text("⏳ Sto preparando il report completo...\nQuesto potrebbe richiedere alcuni secondi.")
    
    try:
        await comando_metriche(update, context)
        await asyncio.sleep(1)
        await comando_portafoglio(update, context)
        await asyncio.sleep(1)
        await comando_grafico_composizione(update, context)
        await update.message.reply_text("✅ Report completo inviato!")
    except Exception as e:
        logger.error(f"Errore in report_completo: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i messaggi quando una modalità è attiva."""
    # Verifica autorizzazione
    if not await check_authorization(update, context):
        return
    
    qrcode_mode = context.user_data.get('qrcode_mode', False)
    investimenti_mode = context.user_data.get('investimenti_mode', False)
    
    # Gestisce modalità QR code
    if qrcode_mode:
        text = update.message.text.strip()
        if not is_valid_url(text):
            await update.message.reply_text(
                "❌ Per favore, invia un link valido (es. https://www.example.com)\n\n"
                "Usa /stop per disattivare la modalità."
            )
            return
        await genera_e_invia_qrcode(update, text)
        return
    
    # Se nessuna modalità è attiva
    if not qrcode_mode and not investimenti_mode:
        await update.message.reply_text(
            "⚠️ Nessuna modalità attiva.\n\n"
            "Usa /qrcode per QR code o /investimenti per investimenti.\n"
            "Usa /help per informazioni."
        )
        return


def main():
    """Funzione principale per avviare il bot."""
    if not BOT_TOKEN:
        logger.error("❌ ERRORE: TELEGRAM_BOT_TOKEN non impostato")
        print("❌ ERRORE: Imposta la variabile d'ambiente TELEGRAM_BOT_TOKEN")
        print("   Esempio: export TELEGRAM_BOT_TOKEN='il_tuo_token'")
        return
    
    # Crea l'applicazione
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registra error handler
    application.add_error_handler(error_handler)
    
    # Registra i gestori (l'ordine è importante - i comandi prima dei messaggi)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("qrcode", qrcode_command))
    application.add_handler(CommandHandler("stop", stop_command))
    
    # Comandi investimenti (se disponibile)
    if INVESTIMENTI_AVAILABLE:
        application.add_handler(CommandHandler("investimenti", investimenti_command))
        application.add_handler(CommandHandler("metriche", comando_metriche))
        application.add_handler(CommandHandler("portafoglio", comando_portafoglio))
        application.add_handler(CommandHandler("grafico_composizione", comando_grafico_composizione))
        application.add_handler(CommandHandler("grafico_andamento", comando_grafico_andamento))
        application.add_handler(CommandHandler("grafico_geografico", comando_grafico_geografico))
        application.add_handler(CommandHandler("grafico_tipologia", comando_grafico_tipologia))
        application.add_handler(CommandHandler("report_completo", comando_report_completo))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Avvia il bot
    logger.info("🤖 Bot avviato!")
    if ALLOWED_USER_IDS:
        logger.info(f"🔒 Accesso limitato a {len(ALLOWED_USER_IDS)} utente/i autorizzato/i")
        print(f"🔒 Bot con accesso limitato a {len(ALLOWED_USER_IDS)} utente/i autorizzato/i")
    else:
        logger.info("🌐 Bot accessibile a tutti gli utenti")
        print("🌐 Bot accessibile a tutti gli utenti")
    
    if INVESTIMENTI_AVAILABLE:
        print("📊 Funzionalità Investimenti: ✅ Disponibile")
    else:
        print("📊 Funzionalità Investimenti: ❌ Non disponibile")
        print("   Installa: pip install kaleido matplotlib pandas plotly yahooquery")
    
    print("🤖 Bot Telegram avviato!")
    print("📡 Gestione errori di rete attiva - il bot si riconnetterà automaticamente")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except KeyboardInterrupt:
        logger.info("Bot fermato dall'utente")
    except Exception as e:
        logger.error(f"Errore fatale: {e}")
        raise


if __name__ == "__main__":
    main()
