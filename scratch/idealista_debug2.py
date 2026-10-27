"""
Test avanzato Idealista - usa uc_gui_click_captcha per bypassare DataDome
"""
from seleniumbase import SB
import time

with SB(uc=True, headless=False) as sb:
    url = "https://www.idealista.it/vendita-case/roma/centro-storico/con-prezzo_600000,camere_2/lista-1/"
    print(f"Aprendo con reconnect: {url}")
    
    sb.uc_open_with_reconnect(url, reconnect_time=6)
    time.sleep(3)
    
    html = sb.get_page_source()
    print(f"HTML dopo reconnect: {len(html):,} caratteri")
    
    # Se ancora DataDome, proviamo il click sul captcha
    if 'captcha-delivery.com' in html or 'DataDome' in html or len(html) < 5000:
        print("DataDome rilevato. Tentativo di bypass con uc_gui_click_captcha...")
        try:
            sb.uc_gui_click_captcha()
            time.sleep(5)
        except Exception as e:
            print(f"uc_gui_click_captcha fallito: {e}")
            
        # Prova anche il bottone del captcha
        try:
            sb.uc_gui_handle_captcha()
            time.sleep(5)
        except Exception as e:
            print(f"uc_gui_handle_captcha fallito: {e}")
    
    html = sb.get_page_source()
    print(f"HTML finale: {len(html):,} caratteri")
    
    if 'captcha-delivery.com' in html:
        print("❌ DataDome ancora attivo - bypass non riuscito")
    else:
        print("✅ Bypass riuscito!")
        with open('scratch/idealista_success.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Salvato in scratch/idealista_success.html")
        # Stampa struttura card
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('article.item')
        print(f"Card trovate: {len(cards)}")
        if cards:
            print("Prima card HTML:")
            print(str(cards[0])[:1000])
