#!/usr/bin/env python3
"""
Applicazione interattiva da terminale per generare QR code e analizzare portafoglio investimenti.
Versione PC - interfaccia testuale senza dipendenze Telegram.
"""

import os
import sys
import logging
import re
from datetime import datetime
from pathlib import Path

# Importa funzioni per QR code
from qrcode_generator import genera_qrcode

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
        PERIODO_DEFAULT,
        GRANULARITA_DEFAULT
    )
except ImportError:
    INV_AVAILABLE = False
    PERIODO_DEFAULT = "1y"
    GRANULARITA_DEFAULT = "1d"

# Importa funzioni per investimenti da utils
try:
    import pandas as pd
    import numpy as np
    from yahooquery import Ticker
    from collections import defaultdict
    from PIL import Image
    
    from utils import (
        carica_dati_portafoglio,
        recupera_dati_mercato,
        calcola_portafoglio_operazioni_tabella,
        calcola_distribuzione_portafoglio
    )
    
    INVESTIMENTI_AVAILABLE = INV_AVAILABLE
except ImportError as e:
    INVESTIMENTI_AVAILABLE = False
    logging.warning(f"⚠️ Funzionalità investimenti non disponibili: {e}")

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Directory per salvare i file generati
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def print_header():
    """Stampa l'header dell'applicazione"""
    print("\n" + "="*60)
    print("  🤖 Applicazione QR Code & Investimenti")
    print("  Versione Terminale - PC")
    print("="*60 + "\n")


def print_menu():
    """Stampa il menu dei comandi disponibili"""
    print("\n" + "-"*60)
    print("📋 COMANDI DISPONIBILI:")
    print("-"*60)
    print("  QR Code:")
    print("    /qrcode <url>          - Genera QR code da URL")
    print("    /qrcode_mode           - Attiva modalità QR code continua")
    print("")
    if INVESTIMENTI_AVAILABLE:
        print("  Investimenti:")
        print("    /investimenti       - Attiva modalità investimenti")
        print("    /metriche           - Mostra metriche portafoglio")
        print("    /portafoglio        - Genera tabella portafoglio")
        print("    /grafico_composizione - Grafico composizione")
        print("    /grafico_andamento  - Grafico andamento titoli")
        print("    /grafico_geografico - Grafico distribuzione geografica")
        print("    /grafico_tipologia  - Grafico distribuzione tipologia")
        print("    /report_completo    - Report completo")
        print("")
    print("  Generali:")
    print("    /help                  - Mostra questo menu")
    print("    /stop                  - Disattiva modalità attive")
    print("    /quit o /exit          - Esci dall'applicazione")
    print("-"*60 + "\n")


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


def salva_immagine(img_bytes: bytes, nome_file: str, descrizione: str = ""):
    """Salva un'immagine come file"""
    file_path = OUTPUT_DIR / nome_file
    try:
        with open(file_path, 'wb') as f:
            f.write(img_bytes)
        print(f"✅ {descrizione} salvata: {file_path.absolute()}")
        return file_path
    except Exception as e:
        print(f"❌ Errore nel salvataggio dell'immagine: {e}")
        return None


def comando_qrcode(args, user_data):
    """Gestisce il comando /qrcode"""
    if not args:
        print("❌ Per favore, fornisci un URL.")
        print("   Esempio: /qrcode https://www.example.com")
        return
    
    url = ' '.join(args)
    
    if not is_valid_url(url):
        print(f"❌ URL non valido: {url}")
        print("   Esempio di URL valido: https://www.example.com")
        return
    
    try:
        print(f"⏳ Sto generando il QR code per: {url}")
        
        # Genera nome file basato su timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"qrcode_{timestamp}.png"
        
        # Genera QR code
        qr_bytes = genera_qrcode(
            url=url,
            dimensione=10,
            bordo=4,
            return_bytes=True
        )
        
        # Salva il file
        file_path = salva_immagine(qr_bytes, nome_file, "QR code")
        if file_path:
            print(f"🔗 URL codificato: {url}")
        
    except Exception as e:
        print(f"❌ Errore durante la generazione del QR code: {e}")
        logger.error(f"Errore in comando_qrcode: {e}", exc_info=True)


def comando_metriche(user_data):
    """Mostra le metriche principali del portafoglio"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva.")
        print("   Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto calcolando le metriche...")
        
        nomi_titoli, operazioni = carica_dati_portafoglio()
        if not nomi_titoli or not operazioni:
            print("❌ Impossibile caricare i dati del portafoglio!")
            return
        
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        report = calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi)
        
        if report.empty or len(report) == 0:
            print("❌ Nessun dato disponibile per il calcolo.")
            return
        
        # Genera e mostra le metriche
        messaggio = genera_metriche_portafoglio(report)
        print("\n" + messaggio + "\n")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in comando_metriche: {e}", exc_info=True)


def comando_portafoglio(user_data):
    """Genera la tabella del portafoglio"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto preparando la tabella del portafoglio...")
        
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        report = calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi)
        
        if report.empty:
            print("❌ Nessun dato disponibile.")
            return
        
        # Genera immagine della tabella
        img_bytes = genera_tabella_portafoglio(report)
        
        # Salva il file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"portafoglio_{timestamp}.png"
        salva_immagine(img_bytes, nome_file, "Tabella portafoglio")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in comando_portafoglio: {e}", exc_info=True)


def comando_grafico_composizione(user_data):
    """Genera il grafico di composizione"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto generando il grafico di composizione...")
        
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        report = calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi)
        
        if report.empty:
            print("❌ Nessun dato disponibile.")
            return
        
        # Genera grafico
        img_bytes = genera_grafico_composizione(report)
        
        # Salva il file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"grafico_composizione_{timestamp}.png"
        salva_immagine(img_bytes, nome_file, "Grafico composizione")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in comando_grafico_composizione: {e}", exc_info=True)


def comando_grafico_andamento(user_data):
    """Genera il grafico di andamento"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto generando il grafico di andamento...")
        print("⏱️ Questo può richiedere alcuni secondi.")
        
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        mappa_nomi = {entry["TICKER"]: entry["nome"] for entry in nomi_titoli}
        
        # Genera grafico
        img_bytes = genera_grafico_andamento(prezzi_dict, mappa_nomi)
        
        # Salva il file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"grafico_andamento_{timestamp}.png"
        salva_immagine(img_bytes, nome_file, "Grafico andamento")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in comando_grafico_andamento: {e}", exc_info=True)


def comando_grafico_geografico(user_data):
    """Genera il grafico geografico"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto generando il grafico geografico...")
        
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        
        try:
            # Genera grafico
            img_bytes = genera_grafico_geografico(nomi_titoli, operazioni, prezzi_dict)
            
            # Salva il file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_file = f"grafico_geografico_{timestamp}.png"
            salva_immagine(img_bytes, nome_file, "Grafico geografico")
        except ValueError as e:
            print(f"❌ {e}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in comando_grafico_geografico: {e}", exc_info=True)


def comando_grafico_tipologia(user_data):
    """Genera il grafico per tipologia"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto generando il grafico per tipologia...")
        
        nomi_titoli, operazioni = carica_dati_portafoglio()
        prezzi_dict = recupera_dati_mercato(nomi_titoli, PERIODO_DEFAULT, GRANULARITA_DEFAULT)
        
        try:
            # Genera grafico
            img_bytes = genera_grafico_tipologia(nomi_titoli, operazioni, prezzi_dict)
            
            # Salva il file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_file = f"grafico_tipologia_{timestamp}.png"
            salva_immagine(img_bytes, nome_file, "Grafico tipologia")
        except ValueError as e:
            print(f"❌ {e}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in comando_grafico_tipologia: {e}", exc_info=True)


def comando_report_completo(user_data):
    """Genera un report completo"""
    if not user_data.get('investimenti_mode', False):
        print("⚠️ Modalità Investimenti non attiva. Usa /investimenti per attivarla.")
        return
    
    try:
        print("⏳ Sto preparando il report completo...")
        print("⏱️ Questo potrebbe richiedere alcuni secondi.\n")
        
        # Metriche
        comando_metriche(user_data)
        print()
        
        # Tabella portafoglio
        comando_portafoglio(user_data)
        print()
        
        # Grafico composizione
        comando_grafico_composizione(user_data)
        print()
        
        print("✅ Report completo generato!")
        print(f"📁 File salvati nella cartella: {OUTPUT_DIR.absolute()}\n")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore in report_completo: {e}", exc_info=True)


def main():
    """Funzione principale - loop interattivo"""
    print_header()
    
    # Verifica funzionalità disponibili
    if INVESTIMENTI_AVAILABLE:
        print("✅ Funzionalità Investimenti: Disponibile")
    else:
        print("⚠️ Funzionalità Investimenti: Non disponibile")
        print("   Installa: pip install matplotlib pandas numpy yahooquery")
    
    print(f"📁 File generati verranno salvati in: {OUTPUT_DIR.absolute()}\n")
    
    # Dizionario per memorizzare lo stato dell'utente
    user_data = {
        'qrcode_mode': False,
        'investimenti_mode': False
    }
    
    print_menu()
    
    # Loop principale interattivo
    while True:
        try:
            # Prompt per l'utente
            prompt = "> "
            if user_data.get('qrcode_mode', False):
                prompt = "[QR Code Mode] > "
            elif user_data.get('investimenti_mode', False):
                prompt = "[Investimenti Mode] > "
            
            # Leggi input dall'utente
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Divide comando e argomenti
            parts = user_input.split(None, 1)
            comando = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Gestione modalità QR code continua
            if user_data.get('qrcode_mode', False) and not comando.startswith('/'):
                # Se siamo in modalità QR code e l'input non è un comando, tratta come URL
                comando = '/qrcode'
                args = [user_input]
            
            # Gestione comandi
            if comando in ['/quit', '/exit']:
                print("\n👋 Arrivederci!\n")
                break
            
            elif comando == '/help':
                print_menu()
            
            elif comando == '/qrcode':
                if args:
                    comando_qrcode(args, user_data)
                else:
                    print("❌ Per favore, fornisci un URL.")
                    print("   Esempio: /qrcode https://www.example.com")
            
            elif comando == '/qrcode_mode':
                user_data['investimenti_mode'] = False
                user_data['qrcode_mode'] = True
                print("✅ Modalità QR code attivata!")
                print("📤 Ora puoi inviare tutti i link che vuoi convertire.")
                print("💡 Invia un link per iniziare, oppure /stop per disattivare.\n")
            
            elif comando == '/stop':
                qrcode_active = user_data.get('qrcode_mode', False)
                investimenti_active = user_data.get('investimenti_mode', False)
                
                user_data['qrcode_mode'] = False
                user_data['investimenti_mode'] = False
                
                if qrcode_active or investimenti_active:
                    print("🛑 Modalità disattivate:")
                    if qrcode_active:
                        print("  • QR code")
                    if investimenti_active:
                        print("  • Investimenti")
                else:
                    print("ℹ️ Nessuna modalità attiva.\n")
            
            elif comando == '/investimenti':
                if not INVESTIMENTI_AVAILABLE:
                    print("❌ Funzionalità investimenti non disponibile.")
                    print("   Installa: pip install matplotlib pandas numpy yahooquery\n")
                    continue
                
                user_data['qrcode_mode'] = False
                user_data['investimenti_mode'] = True
                print("✅ Modalità Investimenti attivata!")
                print("📊 Comandi disponibili:")
                print("  • /metriche - Metriche principali")
                print("  • /portafoglio - Tabella portafoglio")
                print("  • /grafico_composizione - Grafico composizione")
                print("  • /grafico_andamento - Andamento titoli")
                print("  • /grafico_geografico - Distribuzione geografica")
                print("  • /grafico_tipologia - Distribuzione tipologia")
                print("  • /report_completo - Report completo")
                print("💡 Usa /stop per disattivare la modalità.\n")
            
            elif comando == '/metriche':
                comando_metriche(user_data)
            
            elif comando == '/portafoglio':
                comando_portafoglio(user_data)
            
            elif comando == '/grafico_composizione':
                comando_grafico_composizione(user_data)
            
            elif comando == '/grafico_andamento':
                comando_grafico_andamento(user_data)
            
            elif comando == '/grafico_geografico':
                comando_grafico_geografico(user_data)
            
            elif comando == '/grafico_tipologia':
                comando_grafico_tipologia(user_data)
            
            elif comando == '/report_completo':
                comando_report_completo(user_data)
            
            else:
                print(f"❌ Comando sconosciuto: {comando}")
                print("💡 Usa /help per vedere i comandi disponibili.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Arrivederci!\n")
            break
        except EOFError:
            print("\n\n👋 Arrivederci!\n")
            break
        except Exception as e:
            print(f"\n❌ Errore imprevisto: {e}\n")
            logger.error(f"Errore imprevisto: {e}", exc_info=True)


if __name__ == "__main__":
    main()
