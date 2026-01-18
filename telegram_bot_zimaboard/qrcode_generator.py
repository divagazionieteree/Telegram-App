#!/usr/bin/env python3
"""
Script per generare QR code da un link.
"""

import qrcode
import argparse
import sys
import io
from pathlib import Path


def genera_qrcode(url, nome_file="qrcode.png", dimensione=10, bordo=4, return_bytes=False):
    """
    Genera un QR code da un URL.
    
    Args:
        url (str): L'URL da codificare nel QR code
        nome_file (str): Nome del file di output (default: qrcode.png)
        dimensione (int): Dimensione dei box del QR code (default: 10)
        bordo (int): Spessore del bordo (default: 4)
        return_bytes (bool): Se True, ritorna i bytes invece di salvare il file (default: False)
    
    Returns:
        str o bytes: Path del file generato o bytes dell'immagine
    """
    try:
        # Crea l'oggetto QR code
        qr = qrcode.QRCode(
            version=1,  # Controlla la dimensione del QR code (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # ~30% di recupero errori
            box_size=dimensione,
            border=bordo,
        )
        
        # Aggiunge i dati
        qr.add_data(url)
        qr.make(fit=True)
        
        # Crea l'immagine
        img = qr.make_image(fill_color="black", back_color="white")
        
        if return_bytes:
            # Ritorna i bytes dell'immagine
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes.getvalue()
        else:
            # Salva l'immagine
            img.save(nome_file)
            print(f"✓ QR code generato con successo: {nome_file}")
            print(f"  URL codificato: {url}")
            return nome_file
        
    except Exception as e:
        if return_bytes:
            raise Exception(f"Errore durante la generazione del QR code: {e}")
        print(f"✗ Errore durante la generazione del QR code: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Funzione principale."""
    parser = argparse.ArgumentParser(
        description="Genera un QR code da un link",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  %(prog)s https://www.google.com
  %(prog)s https://github.com -o mio_qrcode.png
  %(prog)s https://example.com -s 15 -b 2
        """
    )
    
    parser.add_argument(
        "url",
        help="URL da codificare nel QR code"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="qrcode.png",
        help="Nome del file di output (default: qrcode.png)"
    )
    
    parser.add_argument(
        "-s", "--size",
        type=int,
        default=10,
        help="Dimensione dei box del QR code (default: 10)"
    )
    
    parser.add_argument(
        "-b", "--border",
        type=int,
        default=4,
        help="Spessore del bordo in box (default: 4)"
    )
    
    args = parser.parse_args()
    
    # Genera il QR code
    genera_qrcode(
        url=args.url,
        nome_file=args.output,
        dimensione=args.size,
        bordo=args.border
    )


if __name__ == "__main__":
    main()

