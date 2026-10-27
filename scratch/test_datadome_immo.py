import truststore; truststore.inject_into_ssl()
from seleniumbase import SB
import time

url = "https://www.immobiliare.it/vendita-case/roma/?prezzoMassimo=700000&localiMinimo=2&vrt=41.90151%2C12.469482%3B41.900999%2C12.464333%3B41.899338%2C12.463818%3B41.894994%2C12.467766%3B41.891799%2C12.472057%3B41.890777%2C12.47901%3B41.892758%2C12.481842%3B41.895377%2C12.482786%3B41.896655%2C12.486477%3B41.898188%2C12.490211%3B41.900297%2C12.492571%3B41.902149%2C12.490854%3B41.903108%2C12.488923%3B41.90413%2C12.487507%3B41.905982%2C12.48313%3B41.911763%2C12.477207%3B41.910741%2C12.472959%3B41.905599%2C12.475147%3B41.90151%2C12.469482&fasciaPiano[]=20"

with SB(uc=True, headless=False) as sb:
    print("Apertura URL con reconnect...")
    sb.uc_open_with_reconnect(url, 8)
    time.sleep(5)
    
    html = sb.get_page_source()
    print(f"HTML letto: {len(html):,} caratteri.")
    if len(html) < 10000 or "DataDome" in html or "geo.captcha-delivery.com" in html:
        print("DataDome rilevato! Tento uc_gui_click_captcha()...")
        try:
            sb.uc_gui_click_captcha()
            time.sleep(5)
            html = sb.get_page_source()
            print(f"Dopo uc_gui_click_captcha: {len(html):,} caratteri.")
        except Exception as e:
            print("Errore uc_gui_click_captcha:", e)
            
    if len(html) < 10000:
        print("Ancora bloccato. Attendo 10 secondi per eventuale risoluzione manuale...")
        time.sleep(10)
        html = sb.get_page_source()
        print(f"Dopo attesa: {len(html):,} caratteri.")
