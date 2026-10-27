"""
scrape_idealista.py
Scraper per Idealista.it — integra i risultati nel datalake condiviso.

Strategia:
- SeleniumBase UC mode per bypassare Cloudflare/bot detection
- Parsing HTML delle card nella pagina risultati
- Filtro zone rosse/verdi (stesso sistema di scrape_ev.py)
- Geocoding Nominatim come fallback per indirizzi ambigui
- Merge intelligente nel datalake_poligono.json
"""

import json
import os
import re
import time
import datetime
import requests
import urllib3
from bs4 import BeautifulSoup
from seleniumbase import SB

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATALAKE_PATH = "datalake_poligono.json"
TODAY = datetime.date.today().isoformat()
PREZZO_MAX = 700000
LOCALI_MIN = 2

# URL di ricerca Idealista con poligono come coordinate bounding box
# Zona: Roma Centro Storico, vendita appartamenti, min 2 locali, max 700k
BASE_URL = (
    "https://www.idealista.it/vendita-case/roma/con-prezzo_700000,"
    "camere_2/lista-{page}/?shape=%40%40%40AAgAAAAAAAqEBxQnADdFBIwJBxQBAHgJBhQBAHgJBhQBAHYJBhQDAGwJBhQFAGwJBhQFAFwJBxQFAFkJBhQFAFkJBhQHAEkJBhQHABQJBhQ"
)

# Non usiamo SEARCH_URL come costante singola perché la pagina 1 ha una sintassi diversa

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
    "palombara", "sabina", "frascati", "ciampino", "velletri",
    "caserta", "napoli", "cortina",
]

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
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico|arco|salita|rampa)\s+([^,]+)', title, re.IGNORECASE)
    if match:
        street = match.group(0).strip().lower()
        street = re.sub(r'\s+s\.n\.c|\s+\d+.*$', '', street, flags=re.IGNORECASE).strip()
        return street
    m_in = re.search(r'in\s+([A-Za-zÀ-ÿ\s\'-]+?)(?:,\s*\d+)?,\s*[^,]+,\s*Roma', title, re.IGNORECASE)
    if m_in:
        candidate = m_in.group(1).strip().lower()
        if candidate not in ["vendita", "affitto", "asta"]:
            return candidate
    return ""


def geocode_and_check(title):
    q = extract_street(title)
    if not q:
        return True
    headers = {'User-Agent': 'BI_Immobiliare_Agent/1.0'}
    url = f"https://nominatim.openstreetmap.org/search?q={q}, Roma&format=json&limit=1"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        data = r.json()
        if data:
            return is_point_in_polygon(float(data[0]['lat']), float(data[0]['lon']), POLYGON)
    except Exception:
        pass
    return True


def zone_ammessa(testo):
    z = testo.lower()
    for parola in ZONE_ROSSE:
        if parola in z:
            return False
    return True


def parse_page(html, page_num):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    # Idealista usa article.item con classe "item"
    cards = soup.select('article.item')
    if not cards:
        # Prova con la struttura alternativa
        cards = soup.select('div.item-info-container')

    print(f"   - Trovate {len(cards)} card a pagina {page_num}")

    for card in cards:
        try:
            # Titolo / indirizzo
            titolo_el = card.select_one('a.item-link') or card.select_one('.item-title a')
            if not titolo_el:
                continue
            titolo_raw = titolo_el.get_text(strip=True)
            url_path = titolo_el.get('href', '')
            if not url_path:
                continue
            url = f"https://www.idealista.it{url_path}" if url_path.startswith('/') else url_path

            # Prezzo
            prezzo_el = card.select_one('.item-price') or card.select_one('span.h2-simulated')
            if not prezzo_el:
                continue
            prezzo_text = prezzo_el.get_text(strip=True).replace('.', '').replace('€', '').replace('\xa0', '').strip()
            try:
                prezzo = int(re.sub(r'[^\d]', '', prezzo_text))
            except ValueError:
                continue

            if prezzo <= 0 or prezzo > PREZZO_MAX:
                continue

            # Dettagli (mq, stanze, piano)
            dettagli_els = card.select('.item-detail') or card.select('span.item-detail')
            superficie = None
            stanze = None
            piano = 'N/A'

            for el in dettagli_els:
                testo = el.get_text(strip=True).lower()
                if 'm²' in testo or 'mq' in testo:
                    try:
                        superficie = int(re.sub(r'[^\d]', '', testo))
                    except ValueError:
                        pass
                elif 'local' in testo or 'vano' in testo:
                    try:
                        stanze = int(re.sub(r'[^\d]', '', testo))
                    except ValueError:
                        pass
                elif 'piano' in testo:
                    piano = testo.replace('piano', '').strip().upper() or 'N/A'

            if stanze is None or stanze < LOCALI_MIN:
                continue

            # Zona / indirizzo
            zona_el = card.select_one('.item-detail-location') or card.select_one('span.item-detail')
            zona = zona_el.get_text(strip=True) if zona_el else 'Roma'

            results.append({
                'titolo': titolo_raw,
                'indirizzo_zona': zona,
                'zona': 'Centro Storico',
                'prezzo_attuale': prezzo,
                'superficie': superficie,
                'numero_stanze': stanze,
                'piano': piano,
                'ascensore': 'N/A',
                'terrazza': 'N/A',
                'stato_immobile': 'N/A',
                'contatti': 'N/A',
                'data_pubblicazione': 'N/A',
                'url_sorgente': url,
                'nome_portale': 'idealista.it',
            })

        except Exception as e:
            print(f"   [!] Errore card: {e}")
            continue

    return results


def scrape_idealista():
    all_apts = []

    with SB(uc=True, headless=False) as sb:
        for page in range(1, 15):  # Scansiona fino a 14 pagine (343 annunci / 30 per pagina = ~12 pagine)
            base = "https://www.idealista.it/vendita-case/roma/centro/con-prezzo_700000,bilocali-2,trilocali-3,quadrilocali-4,5-locali-o-piu/"
            
            if page == 1:
                url = base
            else:
                url = base + f"lista-{page}.htm"
                
            print(f"3. Navigazione verso la pagina {page}...")

            try:
                sb.uc_open_with_reconnect(url, reconnect_time=5)
                time.sleep(3)

                html = sb.get_page_source()
                if "captcha-delivery" in html or "DataDome" in html or len(html) < 5000:
                    print("   [!] DataDome rilevato su Idealista. Tentativo di bypass automatico...")
                    try:
                        sb.uc_gui_click_captcha()
                        time.sleep(4)
                    except Exception:
                        pass
                    try:
                        sb.uc_gui_handle_captcha()
                        time.sleep(4)
                    except Exception:
                        pass
                    html = sb.get_page_source()

                if "captcha-delivery" in html or "DataDome" in html or len(html) < 5000:
                    print("   [!] Idealista bloccato da DataDome. Passo oltre per non bloccare gli altri portali.")
                    break
                # Prova a chiudere cookie banner
                try:
                    sb.click('#didomi-notice-agree-button', timeout=3)
                    time.sleep(1)
                except Exception:
                    pass

                html = sb.get_page_source()
                print(f"   - HTML letto pagina {page}: {len(html):,} caratteri.")

                page_apts = parse_page(html, page)

                # Filtro zone rosse e geocoding sul poligono
                filtered = []
                for apt in page_apts:
                    testo_check = f"{apt.get('titolo', '')} {apt.get('indirizzo_zona', '')}"
                    t_lower = apt.get('titolo', '').lower()
                    p_str = str(apt.get('piano', '')).upper()
                    
                    is_c1_c2 = any(x in t_lower for x in ["c1", "c2", "c/1", "c/2", "negozio", "magazzino", "open space", "loft", "ufficio", "studio"])
                    is_asta = 'asta' in t_lower or 'nuda propriet' in t_lower
                    
                    is_low_floor = any(x in p_str for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO']) or \
                                   p_str.strip() in ['T', 'S', 'R', 'S1', 'S2', '1'] or \
                                   '1º' in p_str or '1°' in p_str or '1\ufffd' in p_str
                    
                    if not is_c1_c2 and not is_asta and is_low_floor:
                        print(f"   [Idealista] Escluso (piano basso): {apt['titolo'][:60]} | Piano: {p_str}")
                        continue
                        
                    if not zone_ammessa(testo_check):
                        print(f"   [Idealista] Escluso (zona rossa): {apt['titolo'][:60]}")
                        continue
                    if not geocode_and_check(apt.get('titolo', '')):
                        print(f"   [Idealista] Escluso (geocoding fuori poligono): {apt['titolo'][:60]}")
                        continue
                        
                    filtered.append(apt)

                print(f"   - Estratti {len(filtered)} annunci validi da pagina {page}. Totale progressivo: {len(all_apts) + len(filtered)}")
                all_apts.extend(filtered)

                if len(page_apts) < 10:
                    print("   - Pagina parziale, fine paginazione.")
                    break

                time.sleep(2)

            except Exception as e:
                print(f"   [!] Errore pagina {page}: {e}")
                break

    return all_apts


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
                        stessa_via = (ext.get('indirizzo_zona', '').lower() == apt.get('indirizzo_zona', '').lower())

                    if (stessa_via and
                        str(ext.get('numero_stanze')) == str(apt.get('numero_stanze')) and
                        abs(int(ext.get('superficie') or 0) - int(apt.get('superficie') or 0)) <= 5 and
                        ext.get('prezzo_attuale') == apt.get('prezzo_attuale')):
                        fuzzy_match = True

                if stesso_url or fuzzy_match:
                    found = True
                    if TODAY not in ext.get('date_market_research', []):
                        ext.setdefault('date_market_research', []).append(TODAY)

                    last_price = ext.get('storico_prezzi', [{}])[-1].get('prezzo')
                    if last_price != apt.get('prezzo_attuale') and apt.get('prezzo_attuale', 0) > 0:
                        ext.setdefault('storico_prezzi', []).append({
                            "prezzo": apt.get('prezzo_attuale'),
                            "data_rilevazione": TODAY
                        })
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
            print(f"  + Nuovo: {apt.get('titolo', '')[:60]} | €{apt.get('prezzo_attuale'):,}")

    with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
        json.dump(datalake, f, indent=4, ensure_ascii=False)

    print(f"\n--- RIASSUNTO IDEALISTA ---")
    print(f"Data Esecuzione    : {TODAY}")
    print(f"Nuovi immobili     : {new_added}")
    print(f"Variazioni prezzo  : {price_vars}")
    print(f"Datalake aggiornato: {DATALAKE_PATH}")
    print(f"---------------------------")


if __name__ == "__main__":
    print("1. Avvio scraping Idealista.it...")
    apts = scrape_idealista()
    print(f"\n2. Trovati {len(apts)} annunci validi. Aggiornamento datalake...")
    process_datalake(apts)
