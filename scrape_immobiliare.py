import truststore
truststore.inject_into_ssl()

import json
import os
import re
import random
import datetime
from bs4 import BeautifulSoup
from seleniumbase import SB

DATALAKE_PATH = "datalake_poligono.json"
TODAY = datetime.date.today().isoformat()
MAX_PAGES = 50

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
        # Ignoriamo gli annunci sponsorizzati o in vetrina (spesso finiscono fuori zona)
        card_text = card.get_text(separator=" ").lower()
        if "sponsorizzato" in card_text or "in vetrina" in card_text:
            continue

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
        prezzo = 0
        if price_div:
            price_text = price_div.get_text(separator=" ", strip=True)
            matches = re.findall(r'(\d{1,3}(?:\.\d{3})+)', price_text)
            if matches:
                prezzo = int(matches[0].replace('.', ''))
            else:
                digits = re.sub(r'[^\d]', '', price_text.split(',')[0])
                prezzo = int(digits) if digits else 0
            
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


import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

POLYGON = "41.911763,12.477207;41.910741,12.472959;41.905599,12.475147;41.901510,12.469482;41.900999,12.464333;41.899338,12.463818;41.896763,12.464525;41.895420,12.461398;41.893106,12.462082;41.893483,12.464240;41.890626,12.466556;41.889258,12.465221;41.885729,12.471676;41.886028,12.477003;41.888791,12.479360;41.890777,12.479010;41.892758,12.481842;41.895377,12.482786;41.896655,12.486477;41.898188,12.490211;41.900297,12.492571;41.902149,12.490854;41.903108,12.488923;41.904130,12.487507;41.905982,12.483130;41.911763,12.477207"

def is_point_in_polygon(lat, lon, polygon_str):
    coords = []
    for pair in polygon_str.split(';'):
        if pair.strip():
            lat_p, lon_p = map(float, pair.split(','))
            coords.append((lat_p, lon_p))
            
    x, y = lon, lat
    n = len(coords)
    inside = False
    
    p1x, p1y = coords[0][1], coords[0][0]
    for i in range(n + 1):
        p2x, p2y = coords[i % n][1], coords[i % n][0]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
        
    return inside

def extract_street(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico|corso)\s+([^,]+)', title, re.IGNORECASE)
    if match:
        return match.group(0).strip().lower()
    return ""

ZONE_VERDI = [
    "centro storico", "centro", "tridente",
    "spagna", "trevi", "colonna", "campo marzio",
    "ponte", "parione", "regola",
    "sant eustachio", "sant'eustachio",
    "pantheon", "pigna", "trastevere",
]

ZONE_ROSSE = [
    "torrino",
    "monti", "campitelli", "sant'angelo", "sant angelo",
    "ripa", "borgo", "esquilino", "ludovisi", "termini", "turati",
    "sallustiano", "castro pretorio", "celio",
    "testaccio", "san saba", "prati", "aventino",
    "pigneto", "nomentano", "tuscolano", "quadraro",
    "san giovanni", "appio", "bologna", "policlinico",
    "furio camillo", "re di roma", "colle oppio",
    "conca d'oro", "valli", "città giardino", "tufello",
    "pantano", "ostia", "eur", "tiburtina", "tiburtino", "prenestino",
    "parioli", "flaminio", "salario", "trionfale",
    "aurelio", "gianicolense", "portuense", "ostiense",
]

def zone_ammessa(testo: str) -> bool:
    z = testo.lower()
    for parola in ZONE_ROSSE:
        if parola in z:
            return False
    # Per immobiliare ci fidiamo se non c'è una parola rossa
    return True

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
                stesso_url = apt.get('url_sorgente') in ext.get('url_sorgenti', [])
                
                fuzzy_match = False
                if not stesso_url:
                    via_ext = extract_street(ext.get('titolo', ''))
                    via_apt = extract_street(apt.get('titolo', ''))
                    
                    stessa_via = False
                    if via_ext and via_apt:
                        stessa_via = (via_ext == via_apt)
                    else:
                        stessa_via = (ext.get('indirizzo_zona', '').lower() == apt.get('indirizzo_zona', '').lower()) or \
                                     (apt.get('indirizzo_zona', '').lower() in ext.get('titolo', '').lower()) or \
                                     (ext.get('indirizzo_zona', '').lower() in apt.get('titolo', '').lower())

                    if (stessa_via and
                        ext.get('zona') == apt.get('zona') and
                        str(ext.get('piano')) == str(apt.get('piano')) and
                        str(ext.get('numero_stanze')) == str(apt.get('numero_stanze')) and
                        abs(int(ext.get('superficie', 0)) - int(apt.get('superficie', 0))) <= 5 and
                        ext.get('prezzo_attuale') == apt.get('prezzo_attuale')):
                        fuzzy_match = True

                if stesso_url or fuzzy_match:
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

                    if ext.get('stato_annuncio') != 'Scartato':
                        ext['stato_annuncio'] = "Attivo"
                    if 'data_rimozione' in ext:
                        del ext['data_rimozione']
                    break
            except Exception:
                pass

        if not found and apt.get('prezzo_attuale', 0) > 0:
            t_lower = apt.get('titolo', '').lower()
            p_str = str(apt.get('piano', '')).upper()
            
            is_c1_c2 = any(x in t_lower for x in ["c1", "c2", "c/1", "c/2", "negozio", "magazzino", "open space", "loft", "ufficio", "studio"])
            is_asta = 'asta' in t_lower or 'nuda propriet' in t_lower
            
            is_low_floor = any(x in p_str for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO']) or \
                           p_str.strip() in ['T', 'S', 'R', 'S1', 'S2', '1'] or \
                           '1º' in p_str or '1°' in p_str or '1\ufffd' in p_str
            
            # Exclude only if normal apartment and low floor, or out of zone
            if (not is_c1_c2 and not is_asta and is_low_floor) or not zone_ammessa(apt.get('titolo', '')):
                print(f"  [!] Escluso (piano basso o zona rossa): {apt.get('titolo', '')[:60]}")
                continue
                
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

    # CASO C: Annunci non visti oggi → Non più visibile (solo quelli immobiliare.it)
    not_visible = 0
    for ext in datalake:
        if (ext.get('stato_annuncio') == "Attivo" 
                and ext.get('nome_portale') == "immobiliare.it" 
                and TODAY not in ext.get('date_market_research', [])):
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

        # Warm-up: apertura homepage per ottenere cookie di sessione puliti
        try:
            print("   - Apertura homepage per stabilire sessione...")
            sb.open("https://www.immobiliare.it/")
            sb.sleep(random.uniform(2.5, 4.0))
            for selector in ['button#didomi-notice-agree-button', 'button.agree-btn',
                             'button[data-testid="accept-btn"]', 'a.cc-btn.cc-allow']:
                if sb.is_element_visible(selector):
                    sb.click(selector)
                    print("   - Cookie banner homepage chiuso.")
                    sb.sleep(random.uniform(1.5, 2.5))
                    break
        except Exception as e:
            print(f"   [!] Nota apertura homepage: {e}")

        url_base = "https://www.immobiliare.it/vendita-case/roma/?prezzoMassimo=700000&localiMinimo=2&vrt=41.911763%2C12.477207%3B41.910741%2C12.472959%3B41.905599%2C12.475147%3B41.901510%2C12.469482%3B41.900999%2C12.464333%3B41.899338%2C12.463818%3B41.896763%2C12.464525%3B41.895420%2C12.461398%3B41.893106%2C12.462082%3B41.893483%2C12.464240%3B41.890626%2C12.466556%3B41.889258%2C12.465221%3B41.885729%2C12.471676%3B41.886028%2C12.477003%3B41.888791%2C12.479360%3B41.890777%2C12.479010%3B41.892758%2C12.481842%3B41.895377%2C12.482786%3B41.896655%2C12.486477%3B41.898188%2C12.490211%3B41.900297%2C12.492571%3B41.902149%2C12.490854%3B41.903108%2C12.488923%3B41.904130%2C12.487507%3B41.905982%2C12.483130%3B41.911763%2C12.477207&fasciaPiano[]=20"
        page = 1
        max_pages = MAX_PAGES

        while page <= max_pages:
            try:
                url = url_base if page == 1 else f"{url_base}&pag={page}"
                print(f"3. Navigazione verso la pagina {page}...")
                sb.open(url)
                sb.sleep(random.uniform(4.0, 7.0))

                # Movimento del mouse subito dopo il caricamento (simula l'utente che "guarda" la pagina)
                human_mouse_move(sb)
                sb.sleep(random.uniform(2.0, 4.0))

                # Scroll lento verso il basso (come un utente che legge)
                for _ in range(5):
                    sb.execute_script(f"window.scrollBy(0, {random.randint(200, 500)});")
                    sb.sleep(random.uniform(1.5, 3.0))

                # Torna su
                sb.execute_script("window.scrollTo(0, 0);")
                sb.sleep(random.uniform(2.0, 3.5))

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
                    sb.sleep(random.uniform(2.0, 3.5))
                    human_mouse_move(sb)

                page_html = sb.get_page_source()
                print(f"   - HTML letto pagina {page}: {len(page_html):,} caratteri.")

                if "captcha-delivery" in page_html or "DataDome" in page_html or len(page_html) < 5000:
                    print("   [!] Schermata di verifica DataDome rilevata su Immobiliare.it.")

                soup = BeautifulSoup(page_html, "html.parser")
                print("   - Estrazione dati dalle card...")
                page_apts = extract_cards_from_listing(soup)
                
                if not page_apts:
                    print(f"   - Nessun annuncio valido trovato a pagina {page}. Termino paginazione.")
                    break
                    
                new_apts.extend(page_apts)
                print(f"   - Estratti {len(page_apts)} annunci da pagina {page}. Totale progressivo: {len(new_apts)}")
                
                if len(page_apts) < 25:
                    print(f"   - Pagina parziale ({len(page_apts)} < 25 annunci). Fine risultati.")
                    break

                page += 1
            except Exception as e:
                print(f"   [!] Errore durante la navigazione di pagina {page}: {e}")
                print("   - Salvo comunque gli annunci estratti finora.")
                break

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
