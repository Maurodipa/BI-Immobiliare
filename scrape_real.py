import truststore
truststore.inject_into_ssl()

import json
import os
import re
import random
import datetime
from bs4 import BeautifulSoup
from seleniumbase import SB

DATALAKE_PATH = "datalake_roma.json"
TODAY = datetime.date.today().isoformat()

def extract_number(text):
    if not text:
        return 0
    num = "".join([c for c in text if c.isdigit()])
    return int(num) if num else 0

def human_mouse_move(sb):
    """Simula movimenti casuali del mouse sulla pagina"""
    for _ in range(random.randint(2, 4)):
        x = random.randint(100, 900)
        y = random.randint(100, 600)
        sb.execute_script(f"""
            document.dispatchEvent(new MouseEvent('mousemove', {{
                clientX: {x}, clientY: {y}, bubbles: true
            }}));
        """)
        sb.sleep(random.uniform(0.1, 0.4))

def extract_cards_from_listing(soup):
    """
    Estrae i dati direttamente dalle card nella pagina lista,
    evitando di entrare nei singoli annunci (più sicuro contro il ban).
    """
    apts = []
    
    # Le card degli annunci sono solitamente in elementi li con classe ListItem_item__card__skphy
    # o div con Property_card__4bzXx
    cards = soup.find_all(["li", "div"], class_=re.compile(r'ListItem_item__card|Property_card'))
    
    seen_urls = set()

    for card in cards:
        # Link e Titolo
        title_a = card.find("a", class_=re.compile(r'Title_title'))
        if not title_a:
            continue
            
        href = title_a.get("href", "")
        if "/annunci/" not in href or href in seen_urls:
            continue
        seen_urls.add(href)
        
        titolo = title_a.get_text(strip=True)
        
        # Prezzo
        price_div = card.find("div", class_=re.compile(r'Price_price'))
        if price_div:
            price_text = price_div.get_text(strip=True)
            # Rimuoviamo la parte decimale (es. ",00") se presente
            price_text = price_text.split(',')[0]
            prezzo = int(re.sub(r'[^\d]', '', price_text)) if re.sub(r'[^\d]', '', price_text) else 0
        else:
            prezzo = 0
            
        # Feature list da aria-label (mq, locali, piano, ascensore)
        superficie = 0
        stanze = 0
        piano = "N/A"
        ascensore = "No"
        
        features = card.find_all("div", class_=re.compile(r'FeatureList_item'))
        for f in features:
            label = f.get("aria-label", "")
            if not label:
                continue
                
            label_lower = label.lower()
            if "m²" in label_lower or "mq" in label_lower or "m2" in label_lower:
                sqm_m = re.search(r'(\d+)', label_lower)
                if sqm_m: superficie = int(sqm_m.group(1))
            elif "local" in label_lower or "stanz" in label_lower:
                rooms_m = re.search(r'(\d+)', label_lower)
                if rooms_m: stanze = int(rooms_m.group(1))
            elif "piano" in label_lower:
                piano_m = re.search(r'piano\s*([a-zA-Z0-9]{1,3})', label_lower)
                if piano_m: piano = piano_m.group(1).upper()
            elif "ascensore" in label_lower:
                ascensore = "Sì"

        # Zona (estratta dal titolo o dal testo sottostante)
        indirizzo_zona = "Roma Centro"
        if "," in titolo:
            parts = titolo.split(",")
            if len(parts) > 1:
                indirizzo_zona = parts[-2].strip()
        
        terrazza = "No" # Nella lista non è sempre visibile

        if prezzo == 0 and superficie == 0:
            continue

        apt = {
            "titolo": titolo,
            "indirizzo_zona": indirizzo_zona,
            "zona": "Centro Storico",
            "prezzo_attuale": prezzo,
            "superficie": superficie,
            "numero_stanze": stanze,
            "piano": piano,
            "ascensore": ascensore,
            "terrazza": terrazza,
            "stato_immobile": "N/A",
            "contatti": "N/A",
            "data_pubblicazione": "N/A",
            "url_sorgente": href,
            "nome_portale": "immobiliare.it"
        }
        apts.append(apt)
        print(f"  - {titolo[:50]} | €{prezzo:,} | {superficie}mq | {stanze} loc | Piano {piano}")

    return apts


def process_datalake(new_apts):
    if os.path.exists(DATALAKE_PATH):
        with open(DATALAKE_PATH, "r", encoding="utf-8") as f:
            datalake = json.load(f)
    else:
        datalake = []

    new_added = 0
    price_vars = 0

    for apt in new_apts:
        found = False
        for ext in datalake:
            try:
                # Confrontiamo anche la via / indirizzo_zona per evitare falsi positivi tra quartieri/vie diverse
                stessa_via = (ext.get('indirizzo_zona', '').lower() == apt.get('indirizzo_zona', '').lower()) or \
                             (apt.get('indirizzo_zona', '').lower() in ext.get('titolo', '').lower()) or \
                             (ext.get('indirizzo_zona', '').lower() in apt.get('titolo', '').lower())

                if (stessa_via and
                    ext.get('zona') == apt.get('zona') and
                    str(ext.get('piano')) == str(apt.get('piano')) and
                    str(ext.get('numero_stanze')) == str(apt.get('numero_stanze')) and
                    abs(int(ext.get('superficie', 0)) - int(apt.get('superficie', 0))) <= 5):

                    found = True
                    if TODAY not in ext.get('date_market_research', []):
                        ext.setdefault('date_market_research', []).append(TODAY)

                    last_price = ext.get('storico_prezzi', [{}])[-1].get('prezzo')
                    if last_price != apt.get('prezzo_attuale') and apt.get('prezzo_attuale', 0) > 0:
                        ext.setdefault('storico_prezzi', []).append({"prezzo": apt.get('prezzo_attuale'), "data_rilevazione": TODAY})
                        ext["prezzo_attuale"] = apt.get('prezzo_attuale')
                        price_vars += 1

                    if apt.get('url_sorgente') not in ext.get('url_sorgenti', []):
                        ext.setdefault('url_sorgenti', []).append(apt.get('url_sorgente'))

                    ext['stato_annuncio'] = "Attivo"
                    if 'data_rimozione' in ext:
                        del ext['data_rimozione']
                    break
            except Exception:
                pass

        if not found and apt.get('prezzo_attuale', 0) > 0:
            new_record = {
                "titolo": apt.get('titolo'),
                "indirizzo_zona": apt.get('indirizzo_zona'),
                "zona": apt.get('zona'),
                "prezzo_attuale": apt.get('prezzo_attuale'),
                "superficie": apt.get('superficie'),
                "numero_stanze": apt.get('numero_stanze'),
                "piano": apt.get('piano'),
                "ascensore": apt.get('ascensore'),
                "terrazza": apt.get('terrazza'),
                "stato_immobile": apt.get('stato_immobile'),
                "contatti": apt.get('contatti'),
                "data_pubblicazione": apt.get('data_pubblicazione'),
                "url_sorgenti": [apt.get('url_sorgente')],
                "nome_portale": apt.get('nome_portale'),
                "stato_annuncio": "Attivo",
                "date_market_research": [TODAY],
                "storico_prezzi": [{"prezzo": apt.get('prezzo_attuale'), "data_rilevazione": TODAY}]
            }
            datalake.append(new_record)
            new_added += 1

    # CASO C: Annunci non visti oggi → Non più visibile
    not_visible = 0
    for ext in datalake:
        if ext.get('stato_annuncio') == "Attivo" and TODAY not in ext.get('date_market_research', []):
            ext['stato_annuncio'] = "Non più visibile"
            ext['data_rimozione'] = TODAY
            not_visible += 1

    with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
        json.dump(datalake, f, indent=4, ensure_ascii=False)

    return new_added, price_vars, not_visible


def scrape():
    new_apts = []
    print("1. Inizializzazione browser stealth...")

    with SB(uc=True, headless=False) as sb:
        print("2. CONNESSIONE RIUSCITA! Browser controllato da Python.")

        url = "https://www.immobiliare.it/vendita-case/roma/centro-storico/?criterio=rilevanza&prezzoMassimo=600000&localiMinimo=3&pianoMinimo=2&ascensore=1"
        print(f"3. Navigazione verso la pagina di ricerca...")
        sb.uc_open_with_reconnect(url, 6)
        sb.sleep(random.uniform(3.0, 5.0))

        # Movimento del mouse subito dopo il caricamento (simula l'utente che "guarda" la pagina)
        human_mouse_move(sb)
        sb.sleep(random.uniform(1.0, 2.0))

        # Scroll lento verso il basso (come un utente che legge)
        for _ in range(4):
            sb.execute_script(f"window.scrollBy(0, {random.randint(200, 500)});")
            sb.sleep(random.uniform(1.0, 2.5))

        # Torna su
        sb.execute_script("window.scrollTo(0, 0);")
        sb.sleep(random.uniform(1.5, 2.5))

        # Chiudi il pop-up cookies se appare (con un ritardo "umano")
        for selector in ['button#didomi-notice-agree-button', 'button.agree-btn',
                         'button[data-testid="accept-btn"]', 'a.cc-btn.cc-allow']:
            if sb.is_element_visible(selector):
                sb.sleep(random.uniform(1.0, 2.0))
                sb.click(selector)
                print("   - Cookie banner chiuso.")
                sb.sleep(random.uniform(2.0, 3.0))
                break

        # Chiudi eventuali popup/modal "Salva ricerca"
        for close_sel in ['button[aria-label="close"]', 'button.close', '[data-testid="modal-close"]',
                           'button.in-modal__close', '.nd-modal__close']:
            if sb.is_element_visible(close_sel):
                sb.sleep(random.uniform(0.5, 1.0))
                sb.click(close_sel)
                print("   - Popup chiuso.")
                sb.sleep(random.uniform(1.0, 2.0))
                break

        # Secondo scroll per caricare tutte le card (lazy loading)
        for _ in range(3):
            sb.execute_script(f"window.scrollBy(0, {random.randint(400, 800)});")
            sb.sleep(random.uniform(1.5, 3.0))
            human_mouse_move(sb)

        page_html = sb.get_page_source()
        print(f"4. HTML letto: {len(page_html):,} caratteri.")

        soup = BeautifulSoup(page_html, "html.parser")
        print("5. Estrazione dati dalle card degli annunci (senza entrare nei singoli link)...")
        new_apts = extract_cards_from_listing(soup)
        print(f"6. Estratti {len(new_apts)} annunci validi dalla pagina lista.")

    return new_apts


if __name__ == "__main__":
    new_apts = scrape()

    if not new_apts:
        print("Nessun annuncio estratto. Controlla la finestra di Chrome per eventuali blocchi.")
    else:
        new_added, price_vars, not_visible = process_datalake(new_apts)

        print("\n--- RIASSUNTO MARKET RESEARCH ---")
        print(f"Data Esecuzione    : {TODAY}")
        print(f"Nuovi immobili     : {new_added}")
        print(f"Variazioni prezzo  : {price_vars}")
        print(f"Non più visibili   : {not_visible}")
        print(f"Datalake aggiornato: {DATALAKE_PATH}")
        print("---------------------------------")
