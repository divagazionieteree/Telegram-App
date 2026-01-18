"""
Modulo di utilità per l'applicazione Portafoglio Investimenti
Contiene tutte le funzioni per il caricamento dati, calcoli e visualizzazioni
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import time
import json
import os
import logging
from yahooquery import Ticker
from collections import defaultdict

# Nota: Plotly e Streamlit sono stati rimossi - le funzioni che li usavano non sono più usate dal bot Telegram
# Se servono per la versione Streamlit, reinstalla plotly e streamlit separatamente

# Configura logging per sostituire Streamlit
logger = logging.getLogger(__name__)

# Cache semplice in memoria (sostituisce @st.cache_data)
_cache_data = {}
_cache_timestamps = {}

def _get_cache_key(func_name, *args, **kwargs):
    """Genera una chiave di cache"""
    import hashlib
    key = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key.encode()).hexdigest()

def _is_cache_valid(cache_key, ttl=3600):
    """Verifica se la cache è ancora valida"""
    if cache_key not in _cache_timestamps:
        return False
    age = time.time() - _cache_timestamps[cache_key]
    return age < ttl

def cache_data(ttl=3600):
    """Decoratore di cache semplice (sostituisce @st.cache_data)"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = _get_cache_key(func.__name__, *args, **kwargs)
            if _is_cache_valid(cache_key, ttl):
                return _cache_data[cache_key]
            result = func(*args, **kwargs)
            _cache_data[cache_key] = result
            _cache_timestamps[cache_key] = time.time()
            return result
        return wrapper
    return decorator


@cache_data(ttl=3600)  # Cache per 1 ora
def carica_dati_portafoglio():
    """Carica i dati del portafoglio dal file JSON"""
    # Cerca il file in più posizioni (directory corrente e /app/data per Docker)
    possibili_paths = ['portafoglio_data.json', '/app/data/portafoglio_data.json', 'data/portafoglio_data.json']
    file_path = None
    
    for path in possibili_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    try:
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['nomi_titoli'], data['operazioni']
    except FileNotFoundError:
        pass
    except json.JSONDecodeError as e:
        logger.error(f"❌ Errore nel parsing del file JSON: {e}")
        return [], []
    except Exception as e:
        logger.error(f"❌ Errore nel caricamento dei dati: {e}")
        return [], []
    
    # Se non trovato, crea un file di esempio
    logger.warning("⚠️ File 'portafoglio_data.json' non trovato!")
    logger.info("📝 Creo un file di esempio con dati demo...")
    
    # Crea file JSON di esempio
    dati_esempio = {
        "nomi_titoli": [
            {
                "nome": "Amundi MSCI World UCITS ETF Acc",
                "ISIN": "IE000BI8OT95.SG",
                "TICKER": "MWRD.MI",
                "TER": 0.10,
                "link": "https://www.justetf.com/it/etf-profile.html?isin=IE000BI8OT95"
            },
            {
                "nome": "Amundi Euro Government Bond 3-5Y UCITS ETF Acc",
                "ISIN": "LU1650488494",
                "TICKER": "EM35.MI",
                "TER": 0.10,
                "link": "https://www.justetf.com/it/etf-profile.html?isin=LU1650488494"
            }
        ],
        "operazioni": [
            {
                "data": "2025-01-02",
                "quote": 100,
                "operazione": "acquisto",
                "titolo": "MWRD.MI"
            },
            {
                "data": "2025-01-06",
                "quote": 50,
                "operazione": "acquisto",
                "titolo": "EM35.MI"
            }
        ]
    }
    
    # Prova a salvare nella directory corrente o in /app/data
    save_paths = ['portafoglio_data.json', '/app/data/portafoglio_data.json', 'data/portafoglio_data.json']
    saved = False
    
    for path in save_paths:
        try:
            # Crea directory se non esiste
            dir_path = os.path.dirname(path) if os.path.dirname(path) else '.'
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(dati_esempio, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ File '{path}' creato con dati di esempio!")
            logger.info("📝 Modifica il file per inserire i tuoi dati reali.")
            saved = True
            return dati_esempio['nomi_titoli'], dati_esempio['operazioni']
        except Exception as e:
            continue
    
    if not saved:
        logger.error(f"❌ Errore nella creazione del file. Prova a creare manualmente 'portafoglio_data.json'")
        return [], []


def normalizza_indice_dataframe(df):
    """Normalizza l'indice di un DataFrame per assicurarsi che sia un DatetimeIndex"""
    try:
        if df.empty:
            return df
        
        # Se l'indice non è già un DatetimeIndex, convertiamolo
        if not isinstance(df.index, pd.DatetimeIndex):
            if isinstance(df.index, pd.MultiIndex):
                # Se è un MultiIndex, prendiamo il livello 'date'
                df.index = df.index.get_level_values('date')
            else:
                # Convertiamo l'indice in DatetimeIndex
                df.index = pd.to_datetime(df.index)
        
        # Gestione timezone: rimuovi timezone se presente
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        return df
    except Exception as e:
        logger.error(f"Errore nella normalizzazione dell'indice: {str(e)}")
        return df

def normalizza_data_operazione(data_op):
    """Normalizza una data di operazione rimuovendo il timezone se presente"""
    try:
        if isinstance(data_op, str):
            data_op = pd.to_datetime(data_op)
        
        # Rimuovi timezone se presente
        if hasattr(data_op, 'tz') and data_op.tz is not None:
            data_op = data_op.tz_localize(None)
        
        return data_op
    except Exception as e:
        logger.error(f"Errore nella normalizzazione della data: {str(e)}")
        return data_op

def rendi_dataframe_arrow_compatibile(df):
    """Rende un DataFrame compatibile con Apache Arrow per Streamlit"""
    try:
        df_copy = df.copy()
        
        # Converti tutte le colonne object in string per evitare problemi con Arrow
        for col in df_copy.columns:
            if df_copy[col].dtype == 'object':
                df_copy[col] = df_copy[col].astype(str)
        
        return df_copy
    except Exception as e:
        logger.error(f"Errore nella conversione Arrow: {str(e)}")
        return df

def trova_data_piu_vicina(df, data_target):
    """Trova la data più vicina nel DataFrame a una data target"""
    try:
        # Lavoriamo su una copia per non modificare l'originale
        df_copy = df.copy()
        
        # Converti tutto in stringhe per evitare problemi di timezone
        if isinstance(data_target, str):
            data_target_str = data_target
        else:
            # Rimuovi timezone se presente
            if hasattr(data_target, 'tz') and data_target.tz is not None:
                data_target = data_target.tz_localize(None)
            data_target_str = data_target.strftime('%Y-%m-%d')
        
        # Converti l'indice in stringhe
        index_str = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10] for date in df_copy.index]
        
        # Trova la data più vicina usando stringhe
        min_diff = float('inf')
        data_effettiva = None
        
        for i, date_str in enumerate(index_str):
            try:
                # Calcola differenza in giorni
                date_obj = pd.to_datetime(date_str)
                target_obj = pd.to_datetime(data_target_str)
                diff_days = abs((date_obj - target_obj).days)
                
                if diff_days < min_diff:
                    min_diff = diff_days
                    data_effettiva = df_copy.index[i]
            except:
                continue
        
        return data_effettiva
    except Exception as e:
        logger.error(f"Errore nel trovare la data più vicina: {str(e)}")
        return None

def calcola_valore_investito(row, prezzi_dict):
    """Calcola il valore investito per un'operazione (quote × prezzo per quota nel giorno dell'investimento)"""
    try:
        ticker = row['titolo']
        data_op = normalizza_data_operazione(row['data'])
        quote = row['quote']
        
        # Se il ticker non è presente nei prezzi, usa l'importo_scambiato se disponibile
        if ticker not in prezzi_dict or prezzi_dict[ticker].empty:
            return row.get('importo_scambiato', 0)
        
        df = prezzi_dict[ticker].copy()
        df = df[["close"]].dropna()
        
        # Trova la data più vicina all'operazione
        data_effettiva = trova_data_piu_vicina(df, data_op)
        if data_effettiva is None:
            return row.get('importo_scambiato', 0)
        
        # Recupera il prezzo di chiusura per quella data
        prezzo = df.loc[data_effettiva, "close"]
        
        # Calcola il valore investito
        valore_investito = quote * prezzo
        
        return round(valore_investito, 2)
        
    except Exception as e:
        # In caso di errore, usa l'importo_scambiato se disponibile
        return row.get('importo_scambiato', 0)

@cache_data(ttl=3600)  # Cache per 1 ora
def estrai_prezzi(val_ticker, val_range, val_dataGranularity):
    """Estrae i prezzi storici di un ticker"""
    try:
        ticker = Ticker(val_ticker)
        df = ticker.history(period=val_range, interval=val_dataGranularity)

        # Estrai il livello data se multi-index
        if isinstance(df.index, pd.MultiIndex):
            df = df.loc[val_ticker]
            df.index = df.index.get_level_values('date')

        # Gestisci il timezone immediatamente dopo aver ottenuto l'indice
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df = df[['close']].dropna()
        
        return df
    except Exception as e:
        logger.error(f"Errore nel recupero dati per {val_ticker}: {str(e)}")
        return pd.DataFrame()


def calcola_portafoglio_operazioni_tabella(operazioni, prezzi_dict, mappa_nomi):
    """Calcola il portafoglio basato sulle operazioni"""
    portafoglio = {}
    righe_report = []

    for op in operazioni:
        ticker = op["titolo"]
        data_op = normalizza_data_operazione(op["data"])
        quote = op["quote"]
        tipo = op["operazione"].lower()

        if ticker not in prezzi_dict or prezzi_dict[ticker].empty:
            continue

        df = prezzi_dict[ticker].copy()
        df = df[["close"]].dropna()

        if ticker not in portafoglio:
            portafoglio[ticker] = []

        # Trova la data più vicina alla data dell'operazione
        data_effettiva = trova_data_piu_vicina(df, data_op)
        if data_effettiva is None:
            logger.warning(f"⚠️ Impossibile trovare data per {ticker}")
            continue
        
        try:
            prezzo = df.loc[data_effettiva, "close"]
        except Exception as e:
            logger.warning(f"⚠️ Errore nel recupero prezzo per {ticker}: {str(e)}")
            continue

        if tipo == "acquisto":
            portafoglio[ticker].append((data_effettiva, quote, prezzo))
        elif tipo == "vendita":
            da_vendere = quote
            while da_vendere > 0 and portafoglio[ticker]:
                data_acq, q_acq, p_acq = portafoglio[ticker][0]
                if q_acq <= da_vendere:
                    da_vendere -= q_acq
                    portafoglio[ticker].pop(0)
                else:
                    portafoglio[ticker][0] = (data_acq, q_acq - da_vendere, p_acq)
                    da_vendere = 0

    totale_iniziale = 0
    totale_attuale = 0
    totale_costi_annuali = 0

    for ticker, posizioni in portafoglio.items():
        if ticker not in prezzi_dict or prezzi_dict[ticker].empty:
            continue
            
        df = prezzi_dict[ticker]
        prezzo_attuale = df["close"].iloc[-1]

        valore_iniziale = sum(q * p for _, q, p in posizioni)
        valore_attuale = sum(q * prezzo_attuale for _, q, _ in posizioni)
        quote_residue = sum(q for _, q, _ in posizioni)

        # Calcolo costi annuali (TER)
        # Trova il TER del titolo dalla lista nomi_titoli
        ter_titolo = 0.10  # Default
        for titolo_info in carica_dati_portafoglio()[0]:
            if titolo_info["TICKER"] == ticker:
                ter_titolo = titolo_info.get("TER", 0.10)
                break
        
        # Calcola i costi annuali (TER applicato al valore attuale)
        costi_annuali = valore_attuale * (ter_titolo / 100)
        
        # Calcola il rendimento netto (sottraendo i costi)
        guadagno_netto = valore_attuale - valore_iniziale - costi_annuali
        rendimento_netto = (guadagno_netto / valore_iniziale) * 100 if valore_iniziale else 0
        rendimento_lordo = ((valore_attuale - valore_iniziale) / valore_iniziale) * 100 if valore_iniziale else 0

        # Calcolo del rendimento medio composto (CAGR)
        # Trova la data del primo acquisto per calcolare il tempo trascorso
        if posizioni:
            # Normalizza tutte le date prima del confronto per evitare TypeError
            posizioni_normalizzate = []
            for data, quote, prezzo in posizioni:
                # Normalizza la data
                if isinstance(data, str):
                    data_norm = pd.to_datetime(data)
                elif isinstance(data, date) and not isinstance(data, datetime):
                    data_norm = datetime.combine(data, datetime.min.time())
                else:
                    data_norm = data
                
                # Rimuovi timezone se presente
                if hasattr(data_norm, 'tz') and data_norm.tz is not None:
                    data_norm = data_norm.tz_localize(None)
                
                posizioni_normalizzate.append((data_norm, quote, prezzo))
            
            prima_data = min(posizioni_normalizzate, key=lambda x: x[0])[0]  # Data del primo acquisto
            data_attuale = datetime.now()
            
            anni_trascorsi = (data_attuale - prima_data).days / 365.25
            
            # Calcola CAGR solo se sono passati almeno 30 giorni e c'è un guadagno
            if anni_trascorsi > (30/365.25) and valore_iniziale > 0 and valore_attuale > valore_iniziale:
                cagr = ((valore_attuale / valore_iniziale) ** (1 / anni_trascorsi) - 1) * 100
            else:
                cagr = 0
        else:
            cagr = 0

        totale_iniziale += valore_iniziale
        totale_attuale += valore_attuale
        totale_costi_annuali += costi_annuali

        nome_titolo = mappa_nomi.get(ticker, ticker)

        righe_report.append({
            "Ticker": ticker,  # Mantieni il ticker originale
            "Nome": nome_titolo,  # Aggiungi il nome completo
            "Quote residue": quote_residue,
            "Prezzo attuale": round(prezzo_attuale, 2),
            "Valore iniziale (€)": round(valore_iniziale, 2),
            "Valore attuale (€)": round(valore_attuale, 2),
            "Guadagno lordo (€)": round(valore_attuale - valore_iniziale, 2),
            "Rendimento lordo (%)": round(rendimento_lordo, 2),
            "Costi annuali (€)": round(costi_annuali, 2),
            "Guadagno netto (€)": round(guadagno_netto, 2),
            "Rendimento netto (%)": round(rendimento_netto, 2),
            "CAGR (%)": round(cagr, 2)
        })

    # Totale portafoglio
    totale_guadagno_lordo = totale_attuale - totale_iniziale
    rendimento_totale_lordo = (totale_guadagno_lordo / totale_iniziale) * 100 if totale_iniziale else 0
    totale_guadagno_netto = totale_guadagno_lordo - totale_costi_annuali
    rendimento_totale_netto = (totale_guadagno_netto / totale_iniziale) * 100 if totale_iniziale else 0

    # Calcolo CAGR totale del portafoglio
    # Trova la data del primo acquisto di tutto il portafoglio
    tutte_le_date = []
    for ticker, posizioni in portafoglio.items():
        if posizioni:
            # Normalizza le date prima del confronto
            posizioni_normalizzate = []
            for data, quote, prezzo in posizioni:
                # Normalizza la data
                if isinstance(data, str):
                    data_norm = pd.to_datetime(data)
                elif isinstance(data, date) and not isinstance(data, datetime):
                    data_norm = datetime.combine(data, datetime.min.time())
                else:
                    data_norm = data
                
                # Rimuovi timezone se presente
                if hasattr(data_norm, 'tz') and data_norm.tz is not None:
                    data_norm = data_norm.tz_localize(None)
                
                posizioni_normalizzate.append((data_norm, quote, prezzo))
            
            prima_data_ticker = min(posizioni_normalizzate, key=lambda x: x[0])[0]
            tutte_le_date.append(prima_data_ticker)
    
    if tutte_le_date:
        prima_data_totale = min(tutte_le_date)
        data_attuale = datetime.now()
        
        # Calcola gli anni trascorsi
        if isinstance(prima_data_totale, str):
            prima_data_totale = pd.to_datetime(prima_data_totale)
        elif isinstance(prima_data_totale, date) and not isinstance(prima_data_totale, datetime):
            # Converti datetime.date in datetime.datetime
            prima_data_totale = datetime.combine(prima_data_totale, datetime.min.time())
        if hasattr(prima_data_totale, 'tz') and prima_data_totale.tz is not None:
            prima_data_totale = prima_data_totale.tz_localize(None)
        
        anni_trascorsi_totale = (data_attuale - prima_data_totale).days / 365.25
        
        # Calcola CAGR totale
        if anni_trascorsi_totale > (30/365.25) and totale_iniziale > 0 and totale_attuale > totale_iniziale:
            cagr_totale = ((totale_attuale / totale_iniziale) ** (1 / anni_trascorsi_totale) - 1) * 100
        else:
            cagr_totale = 0
    else:
        cagr_totale = 0

    righe_report.append({
        "Ticker": "**TOTALE**",
        "Nome": "**TOTALE**",
        "Quote residue": 0,  # Usa 0 invece di stringa vuota
        "Prezzo attuale": 0,  # Usa 0 invece di stringa vuota
        "Valore iniziale (€)": round(totale_iniziale, 2),
        "Valore attuale (€)": round(totale_attuale, 2),
        "Guadagno lordo (€)": round(totale_guadagno_lordo, 2),
        "Rendimento lordo (%)": round(rendimento_totale_lordo, 2),
        "Costi annuali (€)": round(totale_costi_annuali, 2),
        "Guadagno netto (€)": round(totale_guadagno_netto, 2),
        "Rendimento netto (%)": round(rendimento_totale_netto, 2),
        "CAGR (%)": round(cagr_totale, 2)
    })

    return pd.DataFrame(righe_report)


def calcola_portafoglio_per_anno(operazioni, prezzi_dict, nomi_titoli):
    """Calcola le informazioni del portafoglio per ogni anno"""
    try:
        # Trova tutti gli anni disponibili
        date_operazioni = [normalizza_data_operazione(op['data']) for op in operazioni]
        anni_operazioni = set()
        for data_op in date_operazioni:
            if isinstance(data_op, str):
                data_op = pd.to_datetime(data_op)
            if hasattr(data_op, 'year'):
                anni_operazioni.add(data_op.year)
        
        # Trova anni dai prezzi
        anni_prezzi = set()
        for ticker, df in prezzi_dict.items():
            if not df.empty:
                for date_idx in df.index:
                    if hasattr(date_idx, 'year'):
                        anni_prezzi.add(date_idx.year)
        
        # Unisci gli anni
        tutti_gli_anni = sorted(list(anni_operazioni.union(anni_prezzi)))
        
        if not tutti_gli_anni:
            return pd.DataFrame()
        
        # Crea mappa TER per ogni ticker
        mappa_ter = {}
        for titolo_info in nomi_titoli:
            ticker = titolo_info.get("TICKER")
            ter = titolo_info.get("TER", 0.10)
            if ticker:
                mappa_ter[ticker] = ter
        
        data_attuale = datetime.now()
        righe_annuali = []
        
        for anno in tutti_gli_anni:
            # Data inizio anno (1 gennaio)
            data_inizio_anno = datetime(anno, 1, 1)
            data_inizio_anno_str = data_inizio_anno.strftime('%Y-%m-%d')
            
            # Data fine anno (31 dicembre o oggi se è l'ultimo anno)
            if anno == data_attuale.year:
                data_fine_anno = data_attuale
            else:
                data_fine_anno = datetime(anno, 12, 31)
            data_fine_anno_str = data_fine_anno.strftime('%Y-%m-%d')
            
            # 1. Calcola VALORE INIZIALE = valore del portafoglio al 1/01 dell'anno
            # (portafoglio fino al 31/12 dell'anno precedente)
            portafoglio_inizio = {}
            for op in operazioni:
                ticker = op["titolo"]
                data_op = normalizza_data_operazione(op["data"])
                quote = op["quote"]
                tipo = op["operazione"].lower()
                
                if isinstance(data_op, str):
                    data_op = pd.to_datetime(data_op)
                elif isinstance(data_op, date) and not isinstance(data_op, datetime):
                    data_op = datetime.combine(data_op, datetime.min.time())
                if hasattr(data_op, 'tz') and data_op.tz is not None:
                    data_op = data_op.tz_localize(None)
                
                # Applica solo le operazioni fino al 31/12 dell'anno precedente
                if data_op < data_inizio_anno:
                    if ticker not in portafoglio_inizio:
                        portafoglio_inizio[ticker] = []
                    
                    if ticker in prezzi_dict and not prezzi_dict[ticker].empty:
                        df = prezzi_dict[ticker].copy()
                        df = df[["close"]].dropna()
                        
                        data_effettiva = trova_data_piu_vicina(df, data_op)
                        if data_effettiva is not None:
                            try:
                                prezzo = df.loc[data_effettiva, "close"]
                                
                                if tipo == "acquisto":
                                    portafoglio_inizio[ticker].append((data_effettiva, quote, prezzo))
                                elif tipo == "vendita":
                                    da_vendere = quote
                                    while da_vendere > 0 and portafoglio_inizio[ticker]:
                                        data_acq, q_acq, p_acq = portafoglio_inizio[ticker][0]
                                        if q_acq <= da_vendere:
                                            da_vendere -= q_acq
                                            portafoglio_inizio[ticker].pop(0)
                                        else:
                                            portafoglio_inizio[ticker][0] = (data_acq, q_acq - da_vendere, p_acq)
                                            da_vendere = 0
                            except:
                                continue
            
            # Calcola valore iniziale al 1/01
            valore_iniziale = 0
            for ticker, posizioni in portafoglio_inizio.items():
                if ticker in prezzi_dict and not prezzi_dict[ticker].empty and posizioni:
                    df = prezzi_dict[ticker]
                    
                    # Trova il prezzo più vicino al 1/01 dell'anno
                    price = None
                    for i in range(len(df.index)):
                        df_date = df.index[i]
                        if hasattr(df_date, 'year'):
                            if df_date.year < anno or (df_date.year == anno and df_date.month == 1 and df_date.day == 1):
                                price = df['close'].iloc[i]
                            elif df_date.year == anno and df_date.month == 1:
                                # Se non c'è il 1/01, prendi il primo prezzo disponibile di gennaio
                                if price is None:
                                    price = df['close'].iloc[i]
                                break
                    
                    if price is not None:
                        ticker_value = sum(q * price for _, q, _ in posizioni)
                        valore_iniziale += ticker_value
            
            # 2. Calcola SOLDI INSERITI = investimenti fatti durante l'anno
            soldi_inseriti = 0
            for op in operazioni:
                ticker = op["titolo"]
                data_op = normalizza_data_operazione(op["data"])
                quote = op["quote"]
                tipo = op["operazione"].lower()
                
                if isinstance(data_op, str):
                    data_op = pd.to_datetime(data_op)
                elif isinstance(data_op, date) and not isinstance(data_op, datetime):
                    data_op = datetime.combine(data_op, datetime.min.time())
                if hasattr(data_op, 'tz') and data_op.tz is not None:
                    data_op = data_op.tz_localize(None)
                
                # Solo acquisti durante l'anno
                if tipo == "acquisto" and data_op.year == anno and data_op >= data_inizio_anno and data_op <= data_fine_anno:
                    if ticker in prezzi_dict and not prezzi_dict[ticker].empty:
                        df = prezzi_dict[ticker].copy()
                        df = df[["close"]].dropna()
                        
                        data_effettiva = trova_data_piu_vicina(df, data_op)
                        if data_effettiva is not None:
                            try:
                                prezzo = df.loc[data_effettiva, "close"]
                                soldi_inseriti += quote * prezzo
                            except:
                                continue
            
            # 3. Calcola SOLDI PRELEVATI = vendite fatte durante l'anno
            soldi_prelevati = 0
            for op in operazioni:
                ticker = op["titolo"]
                data_op = normalizza_data_operazione(op["data"])
                quote = op["quote"]
                tipo = op["operazione"].lower()
                
                if isinstance(data_op, str):
                    data_op = pd.to_datetime(data_op)
                elif isinstance(data_op, date) and not isinstance(data_op, datetime):
                    data_op = datetime.combine(data_op, datetime.min.time())
                if hasattr(data_op, 'tz') and data_op.tz is not None:
                    data_op = data_op.tz_localize(None)
                
                # Solo vendite durante l'anno
                if tipo == "vendita" and data_op.year == anno and data_op >= data_inizio_anno and data_op <= data_fine_anno:
                    if ticker in prezzi_dict and not prezzi_dict[ticker].empty:
                        df = prezzi_dict[ticker].copy()
                        df = df[["close"]].dropna()
                        
                        data_effettiva = trova_data_piu_vicina(df, data_op)
                        if data_effettiva is not None:
                            try:
                                prezzo = df.loc[data_effettiva, "close"]
                                soldi_prelevati += quote * prezzo
                            except:
                                continue
            
            # 4. Calcola VALORE FINALE = valore del portafoglio alla fine dell'anno
            # Ricostruisci il portafoglio fino alla fine dell'anno
            portafoglio_fine = {}
            for op in operazioni:
                ticker = op["titolo"]
                data_op = normalizza_data_operazione(op["data"])
                quote = op["quote"]
                tipo = op["operazione"].lower()
                
                if isinstance(data_op, str):
                    data_op = pd.to_datetime(data_op)
                elif isinstance(data_op, date) and not isinstance(data_op, datetime):
                    data_op = datetime.combine(data_op, datetime.min.time())
                if hasattr(data_op, 'tz') and data_op.tz is not None:
                    data_op = data_op.tz_localize(None)
                
                # Applica tutte le operazioni fino alla fine dell'anno
                if data_op <= data_fine_anno:
                    if ticker not in portafoglio_fine:
                        portafoglio_fine[ticker] = []
                    
                    if ticker in prezzi_dict and not prezzi_dict[ticker].empty:
                        df = prezzi_dict[ticker].copy()
                        df = df[["close"]].dropna()
                        
                        data_effettiva = trova_data_piu_vicina(df, data_op)
                        if data_effettiva is not None:
                            try:
                                prezzo = df.loc[data_effettiva, "close"]
                                
                                if tipo == "acquisto":
                                    portafoglio_fine[ticker].append((data_effettiva, quote, prezzo))
                                elif tipo == "vendita":
                                    da_vendere = quote
                                    while da_vendere > 0 and portafoglio_fine[ticker]:
                                        data_acq, q_acq, p_acq = portafoglio_fine[ticker][0]
                                        if q_acq <= da_vendere:
                                            da_vendere -= q_acq
                                            portafoglio_fine[ticker].pop(0)
                                        else:
                                            portafoglio_fine[ticker][0] = (data_acq, q_acq - da_vendere, p_acq)
                                            da_vendere = 0
                            except:
                                continue
            
            # Calcola valore finale alla fine dell'anno
            valore_finale = 0
            costi_annuali = 0
            
            for ticker, posizioni in portafoglio_fine.items():
                if ticker in prezzi_dict and not prezzi_dict[ticker].empty and posizioni:
                    df = prezzi_dict[ticker]
                    
                    # Trova il prezzo alla fine dell'anno
                    price = None
                    for i in range(len(df.index) - 1, -1, -1):
                        df_date = df.index[i]
                        if hasattr(df_date, 'year'):
                            if df_date.year < anno or (df_date.year == anno and df_date <= data_fine_anno):
                                price = df['close'].iloc[i]
                                break
                    
                    if price is not None:
                        ticker_value = sum(q * price for _, q, _ in posizioni)
                        valore_finale += ticker_value
                        
                        # Costi annuali (TER)
                        ter_titolo = mappa_ter.get(ticker, 0.10)
                        costi_annuali += ticker_value * (ter_titolo / 100)
            
            # 5. Calcola guadagni/rendimenti solo per l'anno
            # Guadagno = (valore finale - valore iniziale - soldi inseriti + soldi prelevati)
            base_calcolo = valore_iniziale + soldi_inseriti - soldi_prelevati
            if base_calcolo > 0:
                guadagno_anno = valore_finale - base_calcolo
                rendimento_anno = (guadagno_anno / base_calcolo) * 100
                
                # Guadagno netto (sottraendo i costi TER)
                guadagno_netto_anno = guadagno_anno - costi_annuali
                rendimento_netto_anno = (guadagno_netto_anno / base_calcolo) * 100
                
                # Calcola CAGR per l'anno (per un singolo anno, CAGR = rendimento annualizzato)
                # CAGR = ((valore_finale / base_calcolo) ^ (1 / 1) - 1) * 100
                if valore_finale > 0:
                    cagr_anno = ((valore_finale / base_calcolo) ** (1 / 1) - 1) * 100
                else:
                    cagr_anno = 0
                
                # CAGR netto (considerando i costi TER)
                valore_finale_netto = valore_finale - costi_annuali
                if valore_finale_netto > 0:
                    cagr_netto_anno = ((valore_finale_netto / base_calcolo) ** (1 / 1) - 1) * 100
                else:
                    cagr_netto_anno = 0
            else:
                guadagno_anno = 0
                rendimento_anno = 0
                guadagno_netto_anno = 0
                rendimento_netto_anno = 0
                cagr_anno = 0
                cagr_netto_anno = 0
            
            righe_annuali.append({
                "Anno": anno,
                "Valore iniziale (€)": round(valore_iniziale, 2),
                "Soldi inseriti (€)": round(soldi_inseriti, 2),
                "Soldi prelevati (€)": round(soldi_prelevati, 2),
                "Valore finale (€)": round(valore_finale, 2),
                "Guadagno anno (€)": round(guadagno_anno, 2),
                "Rendimento anno (%)": round(rendimento_anno, 2),
                "CAGR anno (%)": round(cagr_anno, 2),
                "Costi annuali (€)": round(costi_annuali, 2),
                "Guadagno netto anno (€)": round(guadagno_netto_anno, 2),
                "Rendimento netto anno (%)": round(rendimento_netto_anno, 2),
                "CAGR netto anno (%)": round(cagr_netto_anno, 2)
            })
        
        return pd.DataFrame(righe_annuali)
        
    except Exception as e:
        logger.error(f"Errore nel calcolo portafoglio per anno: {str(e)}")
        return pd.DataFrame()


def plot_portfolio_trend(operazioni, prezzi_dict):
    """Crea un grafico dell'andamento del portafoglio normalizzato a 100"""
    try:
        # Calcola la data di un anno fa
        data_attuale = datetime.now()
        data_un_anno_fa = data_attuale - timedelta(days=365)
        data_un_anno_fa_str = data_un_anno_fa.strftime('%Y-%m-%d')

        # Funzione disabilitata - richiede Plotly che non è più installato
        # Usa investimenti_generator.genera_grafico_andamento() invece
        logger.error("⚠️ Questa funzione richiede Plotly. Usa la versione matplotlib in investimenti_generator.")
        return None
    except Exception as e:
        logger.error(f"Errore nella creazione del grafico: {str(e)}")
        return None


def plot_portfolio_composition(report_df):
    """Crea un grafico a torta della composizione del portafoglio"""
    # Funzione disabilitata - richiede Plotly che non è più installato
    # Usa investimenti_generator.genera_grafico_composizione() invece
    logger.error("⚠️ Questa funzione richiede Plotly. Usa la versione matplotlib in investimenti_generator.")
    return None

def plot_portfolio_value_daily(operazioni, prezzi_dict):
    """Crea un grafico del valore reale del portafoglio (valore titoli × quote) giorno per giorno"""
    # Funzione disabilitata - richiede Plotly che non è più installato
    # Usa investimenti_generator.genera_grafico_andamento() invece
    logger.error("⚠️ Questa funzione richiede Plotly. Usa la versione matplotlib in investimenti_generator.")
    return None


def plot_rendimento_cagr_daily(operazioni, prezzi_dict, nomi_titoli):
    """Crea un grafico del rendimento netto e CAGR del portafoglio giorno per giorno"""
    # Funzione disabilitata - richiede Plotly che non è più installato
    logger.error("⚠️ Questa funzione richiede Plotly. Usa la versione matplotlib in investimenti_generator.")
    return None


def salva_cache_dati(prezzi_dict, periodo, granularita):
    """Salva i dati di mercato in cache locale"""
    try:
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "periodo": periodo,
            "granularita": granularita,
            "dati": {}
        }
        
        for ticker, df in prezzi_dict.items():
            if not df.empty:
                # Converti tutto in stringhe per evitare problemi di timezone
                index_str = []
                close_values = []
                
                for i, date in enumerate(df.index):
                    try:
                        # Converti la data in stringa in modo sicuro
                        if hasattr(date, 'strftime'):
                            # Se è un oggetto datetime, usa strftime
                            if hasattr(date, 'tz') and date.tz is not None:
                                # Rimuovi timezone se presente
                                date = date.tz_localize(None)
                            date_str = date.strftime('%Y-%m-%d')
                        else:
                            # Se non è datetime, converti in stringa
                            date_str = str(date)[:10]
                        
                        index_str.append(date_str)
                        close_values.append(float(df['close'].iloc[i]))
                    except Exception as e:
                        # Se c'è un errore, salta questa riga
                        continue
                
                # Salva solo se abbiamo dati validi
                if index_str and close_values:
                    cache_data["dati"][ticker] = {
                        "index": index_str,
                        "close": close_values
                    }
        
        # Salva in file
        cache_file = f"cache_mercato_{periodo}_{granularita}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Errore nel salvataggio cache: {str(e)}")
        return False

def carica_cache_dati(periodo, granularita):
    """Carica i dati di mercato dalla cache locale"""
    try:
        cache_file = f"cache_mercato_{periodo}_{granularita}.json"
        
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verifica se la cache è ancora valida (meno di 24 ore)
        cache_timestamp = datetime.fromisoformat(cache_data["timestamp"])
        if datetime.now() - cache_timestamp > timedelta(hours=24):
            return None
        
        # Ricostruisci i DataFrame
        prezzi_dict = {}
        for ticker, data in cache_data["dati"].items():
            df = pd.DataFrame({
                'close': data['close']
            }, index=pd.to_datetime(data['index']))
            prezzi_dict[ticker] = df
        
        return prezzi_dict
    except Exception as e:
        logger.error(f"Errore nel caricamento cache: {str(e)}")
        return None

def aggiorna_dati_mancanti(prezzi_dict_cache, nomi_titoli, periodo, granularita):
    """Aggiorna solo i dati mancanti nella cache"""
    try:
        tickers_richiesti = [titolo["TICKER"] for titolo in nomi_titoli]
        tickers_cache = list(prezzi_dict_cache.keys()) if prezzi_dict_cache else []
        
        # Trova i ticker mancanti
        tickers_mancanti = [ticker for ticker in tickers_richiesti if ticker not in tickers_cache]
        
        if not tickers_mancanti:
            return prezzi_dict_cache
        
        logger.info(f"📥 Aggiornando {len(tickers_mancanti)} ticker mancanti...")
        
        # Recupera solo i dati mancanti
        for ticker in tickers_mancanti:
            prezzi_dict_cache[ticker] = estrai_prezzi(ticker, periodo, granularita)
            time.sleep(0.1)
        
        # Salva la cache aggiornata
        salva_cache_dati(prezzi_dict_cache, periodo, granularita)
        
        return prezzi_dict_cache
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento dati mancanti: {str(e)}")
        return prezzi_dict_cache

def recupera_dati_mercato(nomi_titoli, periodo, granularita):
    """Recupera i dati di mercato per tutti i ticker con cache locale"""
    # Prova a caricare dalla cache
    prezzi_dict_cache = carica_cache_dati(periodo, granularita)
    
    if prezzi_dict_cache is not None:
        logger.info("✅ Dati caricati dalla cache locale")
        
        # Aggiorna i dati mancanti se necessario
        prezzi_dict_aggiornato = aggiorna_dati_mancanti(prezzi_dict_cache, nomi_titoli, periodo, granularita)
        if prezzi_dict_aggiornato != prezzi_dict_cache:
            logger.info("📥 Dati mancanti aggiornati")
        
        return prezzi_dict_aggiornato
    
    # Se non c'è cache valida, recupera da Yahoo Finance
    logger.info("Recuperando i dati di mercato da Yahoo Finance...")
    
    tickers = [titolo["TICKER"] for titolo in nomi_titoli]
    prezzi_dict = {}
    
    for i, ticker in enumerate(tickers):
        logger.info(f"Recuperando dati per {ticker} ({i+1}/{len(tickers)})...")
        prezzi_dict[ticker] = estrai_prezzi(ticker, periodo, granularita)
        time.sleep(0.1)  # Piccola pausa per non sovraccaricare l'API
    
    # Salva in cache
    if salva_cache_dati(prezzi_dict, periodo, granularita):
        logger.info("💾 Dati salvati in cache locale")
    
    return prezzi_dict


def crea_sidebar_configurazioni(nomi_titoli, periodo, granularita):
    """Crea la sidebar con le configurazioni"""
    # Funzione disabilitata - richiede Streamlit che non è più installato
    # Questa funzione è solo per la versione Streamlit, non usata dal bot Telegram
    logger.warning("⚠️ Funzione Streamlit non disponibile. Questa funzione richiede Streamlit.")
    return


def mostra_metriche_principali(report):
    """Mostra le metriche principali del portafoglio"""
    # Funzione disabilitata - richiede Streamlit che non è più installato
    # Questa funzione è solo per la versione Streamlit, non usata dal bot Telegram
    logger.warning("⚠️ Funzione Streamlit non disponibile. Questa funzione richiede Streamlit.")
    return


def crea_tabs_applicazione(operazioni, prezzi_dict, report, mappa_nomi, nomi_titoli):
    """Crea tutti i tab dell'applicazione
    
    Args:
        operazioni: Lista delle operazioni di acquisto/vendita
        prezzi_dict: Dizionario con i prezzi storici dei titoli
        report: DataFrame con il report del portafoglio
        mappa_nomi: Dizionario che mappa i ticker ai nomi completi
        nomi_titoli: Lista dei titoli con le loro caratteristiche
    
    Nota: Questa funzione richiede Plotly e non è disponibile senza Plotly.
    Usa le funzioni matplotlib in investimenti_generator per il bot Telegram.
    """
    logger.error("⚠️ Questa funzione richiede Plotly. Non disponibile senza Plotly.")
    return
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Andamento", "🥧 Composizione", "📋 Dettagli"])
    # ---
    with tab1:
        st.subheader("Panoramica Portafoglio")
        
        # Tabella portafoglio per anno
        st.markdown("### 📊 Portafoglio per Anno")
        report_annuale = calcola_portafoglio_per_anno(operazioni, prezzi_dict, nomi_titoli)
        if not report_annuale.empty:
            report_annuale_display = rendi_dataframe_arrow_compatibile(report_annuale)
            st.dataframe(
                report_annuale_display,
                width='stretch',
                hide_index=True
            )
        else:
            st.info("Nessun dato disponibile per la visualizzazione per anno")
        
        # Grafico del valore reale del portafoglio giorno per giorno
        if prezzi_dict:
            st.markdown("### 💰 Valore Reale del Portafoglio")
            st.info("Questo grafico mostra il valore effettivo di ogni titolo (prezzo × quote) nel tempo, permettendo di confrontare l'andamento di ciascun investimento.")
            plot_portfolio_value_daily(operazioni, prezzi_dict)

    with tab2:
        st.subheader("Andamento Storico")
        
        # Calcola la data di un anno fa
        data_attuale = datetime.now()
        data_un_anno_fa = data_attuale - timedelta(days=365)
        data_un_anno_fa_str = data_un_anno_fa.strftime('%Y-%m-%d')
        
        fig_comparison = go.Figure()
        
        for ticker, df in prezzi_dict.items():
            if df.empty:
                continue
                
            # Trova il prezzo di riferimento (un anno fa)
            prezzi_riferimento = []
            for idx, date in enumerate(df.index):
                date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]
                if date_str >= data_un_anno_fa_str:
                    prezzi_riferimento.append(df['close'].iloc[idx])
                    break
            
            # Se non troviamo dati di un anno fa, usa il primo prezzo disponibile
            if not prezzi_riferimento:
                prezzo_riferimento = df['close'].iloc[0]
            else:
                prezzo_riferimento = prezzi_riferimento[0]
            
            # Normalizza i prezzi a 100 basandosi sul prezzo di riferimento
            prezzi_normalizzati = (df['close'] / prezzo_riferimento) * 100
            
            fig_comparison.add_trace(go.Scatter(
                x=df.index,
                y=prezzi_normalizzati,
                mode='lines',
                name=ticker,
                line=dict(width=2)
            ))
        
        fig_comparison.update_layout(
            title="Andamento normalizzato di tutti i titoli (base 100 = 1 anno fa)",
            xaxis_title="Data",
            yaxis_title="Prezzo normalizzato (base 100)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig_comparison, width='stretch')
        
        # Grafico rendimento netto e CAGR giornaliero
        st.markdown("### 📊 Rendimento Netto e CAGR Giornaliero")
        st.info("Questo grafico mostra il rendimento netto (dopo costi TER) e il CAGR (Compound Annual Growth Rate) del portafoglio per ogni giorno.")
        plot_rendimento_cagr_daily(operazioni, prezzi_dict, nomi_titoli)

    with tab3:
        st.subheader("Composizione del Portafoglio")
        
        # Calcola le distribuzioni geografiche e per tipologia di mercato
        distribuzione_geo, distribuzione_tipo, valore_totale, posizioni_mercato = calcola_distribuzione_portafoglio(nomi_titoli, operazioni, prezzi_dict)
        
        # Mostra il valore totale del portafoglio
        st.metric("💰 Valore Totale del Portafoglio (Prezzi di Mercato)", f"€{valore_totale:,.2f}")
        
        # Calcola anche il valore contabile per confronto
        posizioni_contabili = calcola_posizioni_attuali(operazioni)
        valore_contabile = sum(pos['valore_attuale'] for pos in posizioni_contabili.values())
        differenza = valore_totale - valore_contabile
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("📊 Valore Contabile", f"€{valore_contabile:,.2f}")
        with col_info2:
            st.metric("📈 Differenza", f"€{differenza:,.2f}", delta=f"{differenza/valore_contabile*100:.2f}%" if valore_contabile > 0 else "0%")
        with col_info3:
            st.metric("🔄 Rendimento", f"{differenza/valore_contabile*100:.2f}%" if valore_contabile > 0 else "0%")
        
        # Prima riga: grafici a torta per distribuzione geografica e tipologia
        st.markdown("### 🌍 Distribuzione Geografica e Tipologia di Mercato")
        col1, col2 = st.columns(2)
        
        with col1:
            if distribuzione_geo:
                fig_geo = crea_grafico_torta_geografica(distribuzione_geo)
                st.plotly_chart(fig_geo, width='stretch')
            else:
                st.info("📊 I dati di distribuzione geografica non sono disponibili per tutti i titoli")
        
        with col2:
            if distribuzione_tipo:
                fig_tipo = crea_grafico_torta_tipologia(distribuzione_tipo)
                st.plotly_chart(fig_tipo, width='stretch')
            else:
                st.info("📊 I dati di tipologia di mercato non sono disponibili per tutti i titoli")
        
        # Seconda riga: composizione per titolo e tabella
        st.markdown("### 📊 Composizione per Titolo")
        col3, col4 = st.columns(2)
        
        with col3:
            if not report.empty and len(report) > 1:
                fig_pie = plot_portfolio_composition(report)
                st.plotly_chart(fig_pie, width='stretch')
        
        with col4:
            # Tabella composizione
            if not report.empty and len(report) > 1:
                df_composition = report[report['Ticker'] != '**TOTALE**'].copy()
                df_composition['Percentuale'] = (df_composition['Valore attuale (€)'] / df_composition['Valore attuale (€)'].sum()) * 100
                
                # Ordina in ordine decrescente per percentuale
                df_composition = df_composition.sort_values('Percentuale', ascending=False)
                
                # Assicuriamoci che tutti i valori siano compatibili con Arrow
                df_display = df_composition[['Nome', 'Ticker', 'Valore attuale (€)', 'Percentuale']].round(2)
                df_display = rendi_dataframe_arrow_compatibile(df_display)
                
                st.dataframe(
                    df_display,
                    width='stretch'
                )

    with tab4:
        st.subheader("Dettagli Operazioni e Rendimenti")
        # Tabella completa del portafoglio
        if not report.empty:
            report_display = report.copy()
            # Usa la colonna Nome già presente nel report
            report_display['Titolo'] = report_display['Nome']
            # Sostituisci i valori 0 nella riga totale con stringhe vuote per la visualizzazione
            if len(report_display) > 0:
                totale_mask = report_display['Ticker'] == '**TOTALE**'
                report_display['Quote residue'] = report_display['Quote residue'].astype(object)
                report_display['Prezzo attuale'] = report_display['Prezzo attuale'].astype(object)
                report_display.loc[totale_mask, 'Quote residue'] = ''
                report_display.loc[totale_mask, 'Prezzo attuale'] = ''
            # Rendi compatibile con Arrow
            report_display = rendi_dataframe_arrow_compatibile(report_display)
            # Mostra le colonne in ordine logico
            colonne_principali = ['Titolo', 'Ticker', 'Quote residue', 'Prezzo attuale', 'Valore iniziale (€)', 'Valore attuale (€)']
            colonne_rendimento = ['CAGR (%)', 'Guadagno lordo (€)', 'Rendimento lordo (%)', 'Costi annuali (€)', 'Guadagno netto (€)', 'Rendimento netto (%)']
            colonne = colonne_principali + colonne_rendimento
            st.markdown("### 📊 Dettagli Portafoglio")
            st.dataframe(
                report_display[colonne],
                width='stretch',
                hide_index=True
            )
        # Dettagli operazioni
        st.markdown("### 📋 Storico Operazioni")
        df_operazioni = pd.DataFrame(operazioni)
        df_operazioni['data'] = [normalizza_data_operazione(data) for data in df_operazioni['data']]
        df_operazioni = df_operazioni.sort_values('data', ascending=False)
        # Aggiungi colonna Titolo (nome completo)
        df_operazioni['Titolo'] = df_operazioni['titolo'].map(mappa_nomi).fillna('Nome non disponibile')
        
        # Calcola il valore investito (quote × prezzo per quota nel giorno dell'investimento)
        df_operazioni['Valore investito (€)'] = df_operazioni.apply(
            lambda row: calcola_valore_investito(row, prezzi_dict), axis=1
        )
        
        # Rendi compatibile con Arrow
        df_operazioni = rendi_dataframe_arrow_compatibile(df_operazioni)
        # Mostra le colonne in ordine logico
        colonne_op = ['Titolo', 'titolo', 'data', 'operazione', 'quote', 'importo_scambiato', 'Valore investito (€)']
        st.dataframe(
            df_operazioni[colonne_op],
            width='stretch',
            hide_index=True
        )


def crea_footer():
    """Crea il footer dell'applicazione"""
    # Funzione disabilitata - richiede Streamlit che non è più installato
    # Questa funzione è solo per la versione Streamlit, non usata dal bot Telegram
    logger.warning("⚠️ Funzione Streamlit non disponibile. Questa funzione richiede Streamlit.")
    return


def calcola_posizioni_attuali(operazioni):
    """Calcola le posizioni attuali per ogni titolo"""
    posizioni = defaultdict(lambda: {'quote': 0, 'importo_totale': 0})
    
    for op in operazioni:
        ticker = op['titolo']
        quote = op['quote']
        importo = op['importo_scambiato']
        
        if op['operazione'] == 'acquisto':
            posizioni[ticker]['quote'] += quote
            posizioni[ticker]['importo_totale'] += importo
        elif op['operazione'] == 'vendita':
            posizioni[ticker]['quote'] -= quote
            posizioni[ticker]['importo_totale'] -= importo
    
    # Rimuovi posizioni negative o zero
    posizioni = {k: v for k, v in posizioni.items() if v['quote'] > 0}
    
    # Calcola il valore medio per quota
    for ticker in posizioni:
        if posizioni[ticker]['quote'] > 0:
            posizioni[ticker]['valore_medio_quota'] = posizioni[ticker]['importo_totale'] / posizioni[ticker]['quote']
            posizioni[ticker]['valore_attuale'] = posizioni[ticker]['quote'] * posizioni[ticker]['valore_medio_quota']
    
    return posizioni


def calcola_distribuzione_portafoglio(nomi_titoli, operazioni, prezzi_dict):
    """Calcola la distribuzione geografica e per tipologia di mercato del portafoglio usando i prezzi di mercato attuali"""
    
    # Inizializza dizionari per aggregare le distribuzioni
    distribuzione_geo = defaultdict(float)
    distribuzione_tipo = defaultdict(float)
    
    # Calcola le posizioni attuali con i prezzi di mercato
    posizioni_mercato = calcola_posizioni_mercato_attuali(operazioni, prezzi_dict)
    
    # Calcola il valore totale del portafoglio
    valore_totale = sum(pos['valore_attuale'] for pos in posizioni_mercato.values())
    
    for titolo in nomi_titoli:
        ticker = titolo['TICKER']
        if ticker in posizioni_mercato:
            peso_titolo = posizioni_mercato[ticker]['valore_attuale'] / valore_totale
            
            # Distribuzione geografica
            if 'distribuzione_geografica' in titolo:
                for geo in titolo['distribuzione_geografica']:
                    nazione = geo['nazione']
                    percentuale = geo['percentuale'] / 100
                    distribuzione_geo[nazione] += peso_titolo * percentuale
            
            # Distribuzione per tipologia di mercato
            if 'tipologia_mercato' in titolo:
                for tipo in titolo['tipologia_mercato']:
                    tipo_mercato = tipo['tipo']
                    percentuale = tipo['percentuale'] / 100
                    distribuzione_tipo[tipo_mercato] += peso_titolo * percentuale
    
    return distribuzione_geo, distribuzione_tipo, valore_totale, posizioni_mercato


def calcola_posizioni_mercato_attuali(operazioni, prezzi_dict):
    """Calcola le posizioni attuali per ogni titolo usando i prezzi di mercato attuali"""
    posizioni = defaultdict(lambda: {'quote': 0, 'valore_attuale': 0})
    
    for op in operazioni:
        ticker = op['titolo']
        quote = op['quote']
        
        if op['operazione'] == 'acquisto':
            posizioni[ticker]['quote'] += quote
        elif op['operazione'] == 'vendita':
            posizioni[ticker]['quote'] -= quote
    
    # Rimuovi posizioni negative o zero
    posizioni = {k: v for k, v in posizioni.items() if v['quote'] > 0}
    
    # Calcola il valore attuale usando i prezzi di mercato
    for ticker in posizioni:
        if ticker in prezzi_dict and not prezzi_dict[ticker].empty:
            # Prendi l'ultimo prezzo disponibile
            ultimo_prezzo = prezzi_dict[ticker]['close'].iloc[-1]
            posizioni[ticker]['valore_attuale'] = posizioni[ticker]['quote'] * ultimo_prezzo
            posizioni[ticker]['prezzo_attuale'] = ultimo_prezzo
        else:
            # Se non ci sono prezzi di mercato, usa il valore medio di acquisto
            posizioni[ticker]['valore_attuale'] = 0
            posizioni[ticker]['prezzo_attuale'] = 0
    
    return posizioni


def crea_grafico_torta_geografica(distribuzione_geo):
    """Crea il grafico a torta per la distribuzione geografica"""
    # Funzione disabilitata - richiede Plotly che non è più installato
    # Usa investimenti_generator.genera_grafico_geografico() invece
    logger.error("⚠️ Questa funzione richiede Plotly. Usa la versione matplotlib in investimenti_generator.")
    return None


def crea_grafico_torta_tipologia(distribuzione_tipo):
    """Crea il grafico a torta per la tipologia di mercato"""
    # Funzione disabilitata - richiede Plotly che non è più installato
    # Usa investimenti_generator.genera_grafico_tipologia() invece
    logger.error("⚠️ Questa funzione richiede Plotly. Usa la versione matplotlib in investimenti_generator.")
    return None 