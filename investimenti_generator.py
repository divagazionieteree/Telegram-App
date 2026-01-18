#!/usr/bin/env python3
"""
Modulo per generare metriche, grafici e report del portafoglio investimenti.
Simile a qrcode_generator.py, contiene funzioni riutilizzabili per investimenti.
"""

import io
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional

# Importazioni condizionali
try:
    import pandas as pd
    import numpy as np
    
    # Verifica matplotlib (solo matplotlib, niente Plotly/Kaleido)
    try:
        import matplotlib
        matplotlib.use('Agg')  # Backend senza GUI
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        MATPLOTLIB_AVAILABLE = True
    except ImportError:
        MATPLOTLIB_AVAILABLE = False
        logging.warning("⚠️ Matplotlib non disponibile. Installa con: pip install matplotlib")
    
    INVESTIMENTI_AVAILABLE = True
    KALEIDO_AVAILABLE = False  # Non più necessario
except ImportError as e:
    INVESTIMENTI_AVAILABLE = False
    logging.warning(f"⚠️ Funzionalità investimenti non disponibili: {e}")
    KALEIDO_AVAILABLE = False
    MATPLOTLIB_AVAILABLE = False


# Configurazione default
PERIODO_DEFAULT = "1y"
GRANULARITA_DEFAULT = "1d"


def matplotlib_fig_to_bytes(fig, format='png', dpi=150) -> bytes:
    """
    Converte un grafico matplotlib in bytes.
    
    Args:
        fig: Figura matplotlib da convertire
        format (str): Formato immagine (default: 'png')
        dpi (int): Risoluzione (default: 150)
    
    Returns:
        bytes: Bytes dell'immagine PNG
    
    Raises:
        Exception: Se Matplotlib non è disponibile
    """
    if not MATPLOTLIB_AVAILABLE:
        raise Exception("Matplotlib non disponibile. Installa con: pip install matplotlib")
    
    buf = io.BytesIO()
    fig.savefig(buf, format=format, bbox_inches='tight', dpi=dpi)
    buf.seek(0)
    img_bytes = buf.getvalue()
    buf.close()
    plt.close(fig)
    return img_bytes


def dataframe_to_image(df, title="Tabella") -> bytes:
    """
    Converte un DataFrame in immagine PNG.
    
    Args:
        df: DataFrame da convertire
        title (str): Titolo da mostrare sopra la tabella
    
    Returns:
        bytes: Bytes dell'immagine PNG della tabella
    
    Raises:
        Exception: Se Matplotlib non è disponibile
    """
    if not MATPLOTLIB_AVAILABLE:
        raise Exception("Matplotlib non disponibile. Installa con: pip install matplotlib")
    
    # Limita le righe se troppo lunghe
    max_rows = 15
    if len(df) > max_rows:
        df = df.head(max_rows)
    
    # Usa matplotlib per creare un'immagine della tabella
    fig, ax = plt.subplots(figsize=(14, min(8, len(df) * 0.4 + 1)))
    ax.axis('tight')
    ax.axis('off')
    
    # Formatta il DataFrame per la visualizzazione
    df_display = df.copy()
    # Arrotonda i numeri decimali
    for col in df_display.columns:
        if df_display[col].dtype in ['float64', 'int64']:
            df_display[col] = df_display[col].apply(
                lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}"
            )
    
    table = ax.table(
        cellText=df_display.values,
        colLabels=df_display.columns,
        cellLoc='left',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Stili
    for (i, j), cell in table.get_celld().items():
        if i == 0:  # Header
            cell.set_facecolor('#1f77b4')
            cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor('#f0f2f6' if i % 2 == 0 else 'white')
        cell.set_edgecolor('#cccccc')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Converti in bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()


def genera_metriche_portafoglio(report) -> str:
    """
    Genera un messaggio di testo con le metriche principali del portafoglio.
    
    Args:
        report: DataFrame con il report del portafoglio
    
    Returns:
        str: Messaggio formattato con le metriche
    """
    totale_row = report[report['Ticker'] == '**TOTALE**'].iloc[0] if '**TOTALE**' in report['Ticker'].values else None
    
    if totale_row is None:
        totale_valore = report['Valore attuale (€)'].sum()
        totale_iniziale = report['Valore iniziale (€)'].sum()
        totale_guadagno = totale_valore - totale_iniziale
        rendimento = (totale_guadagno / totale_iniziale * 100) if totale_iniziale > 0 else 0
        messaggio = (
            f"📊 Metriche Portafoglio\n\n"
            f"💰 Valore Totale: € {totale_valore:,.2f}\n"
            f"📈 Guadagno Netto: € {totale_guadagno:,.2f}\n"
            f"📊 Rendimento Netto: {rendimento:.2f}%\n"
            f"\n🕐 Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
    else:
        totale_valore = totale_row['Valore attuale (€)']
        totale_guadagno = totale_row['Guadagno netto (€)']
        rendimento = totale_row['Rendimento netto (%)']
        cagr = totale_row['CAGR (%)']
        costi = totale_row['Costi annuali (€)']
        messaggio = (
            f"📊 Metriche Portafoglio\n\n"
            f"💰 Valore Totale: € {totale_valore:,.2f}\n"
            f"📈 Guadagno Netto: € {totale_guadagno:,.2f}\n"
            f"📊 Rendimento Netto: {rendimento:.2f}%\n"
            f"📉 CAGR: {cagr:.2f}%\n"
            f"💸 Costi Annuali: € {costi:,.2f}\n"
            f"\n🕐 Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
    
    return messaggio


def genera_tabella_portafoglio(report) -> bytes:
    """
    Genera un'immagine della tabella del portafoglio.
    
    Args:
        report: DataFrame con il report del portafoglio
    
    Returns:
        bytes: Bytes dell'immagine PNG della tabella
    """
    colonne_display = ['Nome', 'Ticker', 'Valore attuale (€)', 'Rendimento netto (%)', 'CAGR (%)']
    df_display = (
        report[report['Ticker'] != '**TOTALE**'][colonne_display].copy()
        if '**TOTALE**' in report['Ticker'].values
        else report[colonne_display].copy()
    )
    
    return dataframe_to_image(df_display, "📊 Portafoglio Investimenti")


def genera_grafico_composizione(report) -> bytes:
    """
    Genera un grafico a barre orizzontali della composizione del portafoglio.
    
    Args:
        report: DataFrame con il report del portafoglio
    
    Returns:
        bytes: Bytes dell'immagine PNG del grafico
    
    Raises:
        ImportError: Se le librerie necessarie non sono disponibili
    """
    if not INVESTIMENTI_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        raise ImportError("Librerie per investimenti non disponibili")
    
    # Filtra solo i titoli (esclude il totale)
    df_filtered = report[report['Ticker'] != '**TOTALE**'].copy()
    
    if df_filtered.empty:
        raise ValueError("Nessun dato disponibile per la composizione")
    
    # Ordina per valore attuale decrescente (dal maggiore al minore)
    df_sorted = df_filtered.sort_values('Valore attuale (€)', ascending=True)
    
    # Prepara dati per il grafico a barre orizzontali
    valori = df_sorted['Valore attuale (€)'].values
    etichette = [nome[:50] for nome in df_sorted['Nome']]  # Limita lunghezza nomi
    totale = valori.sum()
    percentuali = [v / totale * 100 for v in valori]
    
    # Crea grafico a barre orizzontali con matplotlib
    fig, ax = plt.subplots(figsize=(12, max(8, len(etichette) * 0.6)))
    
    # Colori per le barre
    colors = plt.cm.Set3(range(len(etichette)))
    
    # Crea le barre orizzontali
    bars = ax.barh(etichette, valori, color=colors, edgecolor='black', linewidth=0.5)
    
    # Aggiungi le etichette con solo percentuali sulle barre
    for i, (bar, val, pct) in enumerate(zip(bars, valori, percentuali)):
        width = bar.get_width()
        # Posiziona il testo dentro la barra se c'è spazio, altrimenti fuori
        if width > totale * 0.05:  # Se la barra è almeno il 5% del totale
            ax.text(width * 0.98, bar.get_y() + bar.get_height() / 2,
                   f'{pct:.1f}%',
                   ha='right', va='center', fontsize=9, fontweight='bold', color='black')
        else:
            ax.text(width + totale * 0.01, bar.get_y() + bar.get_height() / 2,
                   f'{pct:.1f}%',
                   ha='left', va='center', fontsize=9, fontweight='bold', color='black')
    
    # Configurazione del grafico
    ax.set_xlabel('Valore Attuale (€)', fontsize=12, fontweight='bold')
    ax.set_title('Composizione del Portafoglio per Valore Attuale', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Formatta l'asse X con separatori migliaia
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€ {x:,.0f}'))
    
    # Mostra solo percentuali sulle barre (valori già rimossi sopra)
    
    # Spazio per le etichette
    plt.tight_layout()
    
    return matplotlib_fig_to_bytes(fig)


def genera_grafico_andamento(prezzi_dict, mappa_nomi) -> bytes:
    """
    Genera un grafico dell'andamento normalizzato dei titoli.
    
    Args:
        prezzi_dict: Dizionario con i prezzi storici dei titoli
        mappa_nomi: Dizionario che mappa i ticker ai nomi completi
    
    Returns:
        bytes: Bytes dell'immagine PNG del grafico
    
    Raises:
        ImportError: Se le librerie necessarie non sono disponibili
    """
    if not INVESTIMENTI_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        raise ImportError("Librerie per investimenti non disponibili")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    data_attuale = datetime.now()
    data_un_anno_fa = data_attuale - timedelta(days=365)
    data_un_anno_fa_str = data_un_anno_fa.strftime('%Y-%m-%d')
    
    colors = plt.cm.tab10(range(len(prezzi_dict)))
    color_idx = 0
    
    for ticker, df in prezzi_dict.items():
        if df.empty:
            continue
        
        # Trova prezzo di riferimento
        prezzo_riferimento = None
        for idx, date in enumerate(df.index):
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]
            if date_str >= data_un_anno_fa_str:
                prezzo_riferimento = df['close'].iloc[idx]
                break
        
        if prezzo_riferimento is None:
            prezzo_riferimento = df['close'].iloc[0]
        
        # Normalizza i prezzi
        prezzi_normalizzati = (df['close'] / prezzo_riferimento) * 100
        nome = mappa_nomi.get(ticker, ticker)
        
        # Converti l'indice in datetime se necessario
        dates = pd.to_datetime(df.index)
        
        ax.plot(dates, prezzi_normalizzati, label=nome, linewidth=2, color=colors[color_idx % len(colors)])
        color_idx += 1
    
    ax.set_title('Andamento Normalizzato Titoli (Base 100 = 1 anno fa)', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Data', fontsize=12)
    ax.set_ylabel('Prezzo Normalizzato (base 100)', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Formatta le date sull'asse x
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    return matplotlib_fig_to_bytes(fig, dpi=150)


def genera_grafico_geografico(nomi_titoli, operazioni, prezzi_dict) -> bytes:
    """
    Genera un grafico a barre orizzontali della distribuzione geografica.
    
    Args:
        nomi_titoli: Lista dei titoli con le loro caratteristiche
        operazioni: Lista delle operazioni di acquisto/vendita
        prezzi_dict: Dizionario con i prezzi storici dei titoli
    
    Returns:
        bytes: Bytes dell'immagine PNG del grafico
    
    Raises:
        ImportError: Se le librerie necessarie non sono disponibili
        ValueError: Se i dati di distribuzione geografica non sono disponibili
    """
    if not INVESTIMENTI_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        raise ImportError("Librerie per investimenti non disponibili")
    
    from utils import calcola_distribuzione_portafoglio
    
    distribuzione_geo, _, valore_totale, _ = calcola_distribuzione_portafoglio(nomi_titoli, operazioni, prezzi_dict)
    
    if not distribuzione_geo:
        raise ValueError("Dati di distribuzione geografica non disponibili")
    
    # Filtra le nazioni con meno dell'1% e crea la categoria "Altri"
    soglia_minima = 0.01  # 1%
    distribuzione_filtrata = {}
    altri_valore = 0
    
    for nazione, percentuale in distribuzione_geo.items():
        if percentuale >= soglia_minima:
            distribuzione_filtrata[nazione] = percentuale
        else:
            altri_valore += percentuale
    
    # Aggiungi la categoria "Altri" se ci sono nazioni sotto la soglia
    if altri_valore > 0:
        distribuzione_filtrata["Altri"] = altri_valore
    
    # Ordina per percentuale decrescente (dal maggiore al minore)
    sorted_items = sorted(distribuzione_filtrata.items(), key=lambda x: x[1], reverse=False)  # ascending=True per barre orizzontali (maggiore in alto)
    labels = [item[0] for item in sorted_items]
    percentuali = [item[1] * 100 for item in sorted_items]  # Converti in percentuali
    valori_euro = [item[1] * valore_totale for item in sorted_items]  # Valori in euro
    
    # Crea grafico a barre orizzontali con matplotlib
    fig, ax = plt.subplots(figsize=(12, max(8, len(labels) * 0.6)))
    
    # Colori per le barre
    colors = plt.cm.Set3(range(len(labels)))
    
    # Crea le barre orizzontali usando le percentuali
    bars = ax.barh(labels, percentuali, color=colors, edgecolor='black', linewidth=0.5)
    
    # Aggiungi le etichette con solo percentuali sulle barre
    for i, (bar, pct, val) in enumerate(zip(bars, percentuali, valori_euro)):
        width = bar.get_width()
        # Posiziona il testo dentro la barra se c'è spazio, altrimenti fuori
        if width > max(percentuali) * 0.05:  # Se la barra è almeno il 5% del massimo
            ax.text(width * 0.98, bar.get_y() + bar.get_height() / 2,
                   f'{pct:.1f}%',
                   ha='right', va='center', fontsize=9, fontweight='bold', color='black')
        else:
            ax.text(width + max(percentuali) * 0.01, bar.get_y() + bar.get_height() / 2,
                   f'{pct:.1f}%',
                   ha='left', va='center', fontsize=9, fontweight='bold', color='black')
    
    # Configurazione del grafico
    ax.set_xlabel('Percentuale (%)', fontsize=12, fontweight='bold')
    ax.set_title('Distribuzione Geografica del Portafoglio', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Formatta l'asse X con percentuali
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Spazio per le etichette
    plt.tight_layout()
    
    return matplotlib_fig_to_bytes(fig)


def genera_grafico_tipologia(nomi_titoli, operazioni, prezzi_dict) -> bytes:
    """
    Genera un grafico a barre orizzontali della distribuzione per tipologia.
    
    Args:
        nomi_titoli: Lista dei titoli con le loro caratteristiche
        operazioni: Lista delle operazioni di acquisto/vendita
        prezzi_dict: Dizionario con i prezzi storici dei titoli
    
    Returns:
        bytes: Bytes dell'immagine PNG del grafico
    
    Raises:
        ImportError: Se le librerie necessarie non sono disponibili
        ValueError: Se i dati di distribuzione per tipologia non sono disponibili
    """
    if not INVESTIMENTI_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        raise ImportError("Librerie per investimenti non disponibili")
    
    from utils import calcola_distribuzione_portafoglio
    
    _, distribuzione_tipo, valore_totale, _ = calcola_distribuzione_portafoglio(nomi_titoli, operazioni, prezzi_dict)
    
    if not distribuzione_tipo:
        raise ValueError("Dati di distribuzione per tipologia non disponibili")
    
    # Ordina per percentuale decrescente (dal maggiore al minore)
    sorted_items = sorted(distribuzione_tipo.items(), key=lambda x: x[1], reverse=False)  # ascending=True per barre orizzontali (maggiore in alto)
    labels = [item[0] for item in sorted_items]
    percentuali = [item[1] * 100 for item in sorted_items]  # Converti in percentuali
    valori_euro = [item[1] * valore_totale for item in sorted_items]  # Valori in euro
    
    # Crea grafico a barre orizzontali con matplotlib
    fig, ax = plt.subplots(figsize=(12, max(8, len(labels) * 0.6)))
    
    # Colori per le barre
    colors = plt.cm.Pastel1(range(len(labels)))
    
    # Crea le barre orizzontali usando le percentuali
    bars = ax.barh(labels, percentuali, color=colors, edgecolor='black', linewidth=0.5)
    
    # Aggiungi le etichette con solo percentuali sulle barre
    for i, (bar, pct, val) in enumerate(zip(bars, percentuali, valori_euro)):
        width = bar.get_width()
        # Posiziona il testo dentro la barra se c'è spazio, altrimenti fuori
        if width > max(percentuali) * 0.05:  # Se la barra è almeno il 5% del massimo
            ax.text(width * 0.98, bar.get_y() + bar.get_height() / 2,
                   f'{pct:.1f}%',
                   ha='right', va='center', fontsize=9, fontweight='bold', color='black')
        else:
            ax.text(width + max(percentuali) * 0.01, bar.get_y() + bar.get_height() / 2,
                   f'{pct:.1f}%',
                   ha='left', va='center', fontsize=9, fontweight='bold', color='black')
    
    # Configurazione del grafico
    ax.set_xlabel('Percentuale (%)', fontsize=12, fontweight='bold')
    ax.set_title('Tipologia di Mercato del Portafoglio', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Formatta l'asse X con percentuali
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Spazio per le etichette
    plt.tight_layout()
    
    return matplotlib_fig_to_bytes(fig)


# Esporta le funzioni principali
__all__ = [
    'matplotlib_fig_to_bytes',
    'dataframe_to_image',
    'genera_metriche_portafoglio',
    'genera_tabella_portafoglio',
    'genera_grafico_composizione',
    'genera_grafico_andamento',
    'genera_grafico_geografico',
    'genera_grafico_tipologia',
    'INVESTIMENTI_AVAILABLE',
    'KALEIDO_AVAILABLE',  # Mantenuto per compatibilità, ma sempre False
    'MATPLOTLIB_AVAILABLE',
    'PERIODO_DEFAULT',
    'GRANULARITA_DEFAULT',
]
