"""
Test Idealista - navigazione organica dalla homepage
"""
from seleniumbase import SB
from bs4 import BeautifulSoup
import time

with SB(uc=True, headless=False) as sb:
    # Step 1: apri homepage (non dovrebbe triggherare DataDome)
    print("Step 1: Apertura homepage idealista.it...")
    sb.uc_open_with_reconnect("https://www.idealista.it/", reconnect_time=4)
    time.sleep(4)
    
    html = sb.get_page_source()
    print(f"Homepage: {len(html):,} caratteri. DataDome: {'captcha-delivery' in html}")
    
    # Step 2: accetta cookie se presenti
    try:
        sb.click('#didomi-notice-agree-button', timeout=3)
        time.sleep(1)
    except Exception:
        pass
    try:
        sb.click('button[id*="accept"]', timeout=2)
        time.sleep(1)
    except Exception:
        pass

    # Step 3: naviga internamente verso la ricerca
    print("Step 2: Navigazione interna verso la ricerca...")
    target = "https://www.idealista.it/vendita-case/roma/centro-storico/con-prezzo_600000,camere_2/lista-1/"
    sb.execute_script(f"window.location.href = '{target}';")
    time.sleep(5)
    
    html = sb.get_page_source()
    print(f"Ricerca: {len(html):,} caratteri. DataDome: {'captcha-delivery' in html}")
    
    if 'captcha-delivery' not in html and len(html) > 10000:
        print("BYPASS RIUSCITO!")
        with open('scratch/idealista_success.html', 'w', encoding='utf-8') as f:
            f.write(html)
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('article.item')
        print(f"Card trovate: {len(cards)}")
        if cards:
            print("Struttura prima card:")
            print(str(cards[0])[:1500])
    else:
        print("BYPASS NON RIUSCITO - DataDome ancora attivo")
        # Proviamo a vedere la struttura vera della pagina cercando altri selettori
        soup = BeautifulSoup(html, 'html.parser')
        print("Titolo pagina:", soup.title.string if soup.title else "N/A")
