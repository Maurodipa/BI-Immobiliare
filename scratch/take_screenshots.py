import os
from playwright.sync_api import sync_playwright

dest_dir = r"C:\Users\mauro\.gemini\antigravity\brain\175b7fe0-188c-4061-a9c8-745b4b82a986"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    abs_html = os.path.abspath("mappa_interattiva_trastevere.html").replace("\\", "/")
    page.goto(f"file:///{abs_html}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    
    # 1. Chiudi popup se aperto
    page.evaluate("map.closePopup();")
    
    # 2. Mostra Poligono Unificato
    page.evaluate("showUnified();")
    page.wait_for_timeout(3000)
    img_unified = os.path.join(dest_dir, "mappa_poligono_unificato.png")
    page.screenshot(path=img_unified)
    print(f"Salvato {img_unified}")
    
    # 3. Zoom su Trastevere con i 12 vertici
    page.evaluate("""
        showBoth();
        map.closePopup();
        map.fitBounds(layerTrastevere.getBounds(), { padding: [50, 50] });
    """)
    page.wait_for_timeout(3000)
    img_trastevere = os.path.join(dest_dir, "mappa_dettaglio_trastevere.png")
    page.screenshot(path=img_trastevere)
    print(f"Salvato {img_trastevere}")
    
    browser.close()
