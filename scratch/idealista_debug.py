"""
Test di debug per Idealista - verifica cosa restituisce il browser
"""
from seleniumbase import SB
import time

with SB(uc=True, headless=False) as sb:
    url = "https://www.idealista.it/vendita-case/roma/centro-storico/con-prezzo_600000,camere_2/lista-1/"
    print(f"Aprendo: {url}")
    sb.uc_open_with_reconnect(url, reconnect_time=5)
    time.sleep(4)
    
    html = sb.get_page_source()
    print(f"HTML ricevuto: {len(html):,} caratteri")
    print("--- Primi 2000 caratteri ---")
    print(html[:2000])
    
    # Salva per analisi
    with open('scratch/idealista_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\nSalvato in scratch/idealista_debug.html")
