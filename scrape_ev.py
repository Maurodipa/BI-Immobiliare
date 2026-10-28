import truststore
truststore.inject_into_ssl()

import json
import os
import re
import time
import datetime
from bs4 import BeautifulSoup
from seleniumbase import SB

DATALAKE_PATH = "datalake_poligono.json"
TODAY = datetime.date.today().isoformat()
PREZZO_MAX = 700000
LOCALI_MIN = 2
MAX_PAGES = 50
BASE_URL = "https://www.engelvoelkers.com/it/it/proprieta/res/vendita/immobili/lazio/roma?pageSize=18&facets=subTypology:apartment;&facets=commercializationType:buy;"

# ── Filtro zone: lista verde (inclusione) e lista rossa (esclusione) ─
# La lista ROSSA ha priorità assoluta: se la zona contiene anche solo
# una parola rossa, l'annuncio viene scartato. Solo se nessuna parola
# rossa è presente si verifica la lista verde.
# Zone ambigue o generiche (es. solo "Roma") passano se non contengono
# nessuna parola rossa — comportamento sicuro e conservativo.

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
    "ripa", "borgo", "esquilino", "ludovisi",
    "sallustiano", "castro pretorio", "celio",
    "testaccio", "san saba", "prati", "aventino",
    # Macro-zone E&V che corrispondono a rioni fuori zona
    "pigneto", "nomentano", "tuscolano", "quadraro",
    "san giovanni", "appio", "bologna", "policlinico",
    "furio camillo", "re di roma", "colle oppio",
    "conca d'oro", "valli", "città giardino", "tufello",
    "pantano", "ostia", "eur", "tiburtino", "prenestino",
    "parioli", "flaminio", "salario", "trionfale",
    "aurelio", "gianicolense", "portuense", "ostiense",
    "della vittoria", "delle vittorie", "primavalle", "gemelli", "clodio",
    "villaggio azzurro", "spinaceto", "ardeatino", "don bosco", "colle parnaso", "pomezia",
]

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

def geocode_and_check(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico)\s+([^,-]+)', title, re.IGNORECASE)
    q = match.group(0).strip() if match else None
    
    if not q:
        match = re.search(r' a ([A-Z][a-zA-Z\s]+)', title)
        q = match.group(1).strip() if match else None
    if not q:
        match = re.search(r'in zona ([A-Z][a-zA-Z\s]+)', title)
        q = match.group(1).strip() if match else None
        
    if not q: 
        return False # Se la zona non è verde e non c'è un indirizzo chiaro nel titolo, escludiamo
    
    headers = {'User-Agent': 'BI_Immobiliare_Agent/1.0'}
    url = f"https://nominatim.openstreetmap.org/search?q={q}, Roma&format=json&limit=1"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        data = r.json()
        if data:
            return is_point_in_polygon(float(data[0]['lat']), float(data[0]['lon']), POLYGON)
        return False
    except:
        return False
    return False

def zone_ammessa(zona: str) -> bool:
    """
    Restituisce True se la zona è ammessa.
    Logica:
      1. Se la zona contiene una parola ROSSA → False (esclusa)
      2. Se la zona contiene una parola VERDE → True (inclusa)
      3. Altrimenti → True (zona generica, es. "Roma": lasciamo passare)
    """
    z = zona.lower()
    for parola in ZONE_ROSSE:
        if parola in z:
            return False
    for parola in ZONE_VERDI:
        if parola in z:
            return True
    # Zona generica non riconosciuta → includi di default
    return True

# ── Helper già presente in scrape_real.py ────────────────────────────
def extract_street(title):
    match = re.search(
        r'(via|viale|piazza|largo|corso|vicolo|vico)\s+([^,]+)',
        title, re.IGNORECASE
    )
    if match:
        return match.group(0).strip().lower()
    return ""


# ── Estrae listings dal JSON __NEXT_DATA__ ───────────────────────────
def find_listings_arr(obj, depth=0):
    if depth > 15:
        return None
    if isinstance(obj, dict):
        if 'listings' in obj and isinstance(obj['listings'], list) and len(obj['listings']) > 3:
            return obj['listings']
        for v in obj.values():
            r = find_listings_arr(v, depth + 1)
            if r:
                return r
    elif isinstance(obj, list):
        for i in obj:
            r = find_listings_arr(i, depth + 1)
            if r:
                return r
    return None


def extract_cards_ev(src):
    """Estrae appartamenti da una pagina E&V usando __NEXT_DATA__ JSON."""
    soup = BeautifulSoup(src, "html.parser")
    nd = soup.find("script", id="__NEXT_DATA__")
    if not nd:
        print("   [EV] __NEXT_DATA__ non trovato (probabile captcha).")
        return []

    data = json.loads(nd.get_text())
    listings = find_listings_arr(data)
    if not listings:
        print("   [EV] Nessun listing trovato nel JSON.")
        return []

    results = []
    for item in listings:
        l = item.get("listing", {})

        # Filtro città: solo Roma
        address_components = l.get("addressComponents", [])
        city = next((c["text"] for c in address_components if c["placeType"] == "locality"), "")
        if city.lower() != "roma":
            continue

        # Prezzo
        price_data = (l.get("price") or {}).get("salesPrice", {})
        price = price_data.get("min", 0) or 0
        if price == 0 or price > PREZZO_MAX:
            continue

        # Locali
        rooms = (l.get("rooms") or {}).get("min", 0) or 0
        if rooms < LOCALI_MIN:
            continue

        # Superficie
        area = (l.get("area") or {}).get("totalSurface", {}).get("min", 0) or 0

        # Titolo
        title = (l.get("profile") or {}).get("title", "Appartamento")
        title = title.replace("\ufffd", "'").strip()

        # Zona
        neighborhood = next(
            (c["text"] for c in address_components if c["placeType"] == "neighborhood"), ""
        )
        zona = neighborhood if neighborhood else city

        # Filtro zona: lista verde / lista rossa
        if not zone_ammessa(zona):
            print(f"   [EV] Escluso (zona fuori area): {zona} | {title[:40]}")
            continue
            
        # Controllo avanzato con Geocoding (Google Maps / OSM) se la zona è generica e non verificata verde
        is_green = any(parola in zona.lower() for parola in ZONE_VERDI)
        if not is_green:
            if not geocode_and_check(title):
                print(f"   [EV] Escluso (geocoding fuori poligono): {title[:60]}")
                continue

        # ID & URL
        display_id = l.get("displayId", "")
        expose_id = l.get("id", "")
        if expose_id:
            url = f"https://www.engelvoelkers.com/it/it/exposes/{expose_id}"
        else:
            url = f"https://www.engelvoelkers.com/it/it/proprieta/{display_id.lower()}"

        results.append({
            "titolo": title,
            "indirizzo_zona": zona,
            "zona": "Centro Storico",
            "prezzo_attuale": price,
            "superficie": area,
            "numero_stanze": rooms,
            "piano": "N/A",
            "ascensore": "N/A",
            "terrazza": "No",
            "stato_immobile": "N/A",
            "contatti": "N/A",
            "data_pubblicazione": "N/A",
            "url_sorgente": url,
            "nome_portale": "engelvoelkers.com",
        })

    return results


# ── Merge nel datalake (stessa logica di scrape_real.py) ─────────────
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
                    ext["date_market_research"] = ext.get("date_market_research", [])
                    if TODAY not in ext["date_market_research"]:
                        ext["date_market_research"].append(TODAY)

                    if apt["url_sorgente"] not in ext.get("url_sorgenti", []):
                        ext.setdefault("url_sorgenti", []).append(apt["url_sorgente"])

                    if ext.get("prezzo_attuale") != apt.get("prezzo_attuale"):
                        ext.setdefault("storico_prezzi", []).append({
                            "prezzo": apt["prezzo_attuale"],
                            "data_rilevazione": TODAY
                        })
                        ext["prezzo_attuale"] = apt["prezzo_attuale"]
                        price_vars += 1

                    ext["stato_annuncio"] = "Attivo"
                    break
            except Exception:
                continue

        if not found:
            t_lower = apt.get('titolo', '').lower()
            p_str = str(apt.get('piano', '')).upper()
            
            is_c1_c2 = any(x in t_lower for x in ["c1", "c2", "c/1", "c/2", "negozio", "magazzino", "open space", "loft", "ufficio", "studio"])
            is_asta = 'asta' in t_lower or 'nuda propriet' in t_lower
            
            is_low_floor = any(x in p_str for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO']) or \
                           p_str.strip() in ['T', 'S', 'R', 'S1', 'S2', '1'] or \
                           '1º' in p_str or '1°' in p_str or '1\ufffd' in p_str
            
            if not is_c1_c2 and not is_asta and is_low_floor:
                print(f"   [EV] Escluso (piano basso): {apt['titolo'][:60]} | Piano: {p_str}")
                continue
                
            new_record = {
                "titolo": apt.get("titolo"),
                "indirizzo_zona": apt.get("indirizzo_zona"),
                "zona": apt.get("zona"),
                "prezzo_attuale": apt.get("prezzo_attuale"),
                "superficie": apt.get("superficie"),
                "numero_stanze": apt.get("numero_stanze"),
                "piano": apt.get("piano"),
                "ascensore": apt.get("ascensore"),
                "terrazza": apt.get("terrazza"),
                "stato_immobile": apt.get("stato_immobile"),
                "contatti": apt.get("contatti"),
                "data_pubblicazione": apt.get("data_pubblicazione"),
                "url_sorgenti": [apt.get("url_sorgente")],
                "nome_portale": apt.get("nome_portale"),
                "stato_annuncio": "Attivo",
                "date_market_research": [TODAY],
                "storico_prezzi": [{"prezzo": apt.get("prezzo_attuale"), "data_rilevazione": TODAY}]
            }
            datalake.append(new_record)
            new_added += 1

    # Annunci non visti oggi → Non più visibile (solo quelli EV)
    not_visible = 0
    for ext in datalake:
        if (ext.get("stato_annuncio") == "Attivo"
                and ext.get("nome_portale") == "engelvoelkers.com"
                and TODAY not in ext.get("date_market_research", [])):
            ext["stato_annuncio"] = "Non più visibile"
            ext["data_rimozione"] = TODAY
            not_visible += 1

    with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
        json.dump(datalake, f, indent=4, ensure_ascii=False)

    return new_added, price_vars, not_visible


# ── Scraper principale ────────────────────────────────────────────────
def scrape():
    print("1. Inizializzazione browser stealth (Engel & Völkers)...")
    new_apts = []

    with SB(uc=True, headless=False) as sb:
        print("2. CONNESSIONE RIUSCITA!")
        page = 1
        max_pages = MAX_PAGES

        while page <= max_pages:
            url = BASE_URL + f"&page={page}"
            print(f"3. Navigazione pagina {page}...")
            sb.uc_open_with_reconnect(url, 6)
            time.sleep(3)

            src = sb.get_page_source()
            page_apts = extract_cards_ev(src)

            if not page_apts:
                print(f"   - Nessun annuncio valido a pagina {page}. Termino paginazione.")
                break

            new_apts.extend(page_apts)
            print(f"   - Estratti {len(page_apts)} da pagina {page} (tot. progressivo: {len(new_apts)})")
            page += 1

    return new_apts


if __name__ == "__main__":
    start_t = time.time()
    new_apts = scrape()

    if not new_apts:
        print("Nessun annuncio estratto da Engel & Völkers.")
    else:
        new_added, price_vars, not_visible = process_datalake(new_apts)
        elapsed_t = time.time() - start_t
        mins, secs = divmod(elapsed_t, 60)
        dur_str = f"{int(mins)}m {secs:04.1f}s ({elapsed_t:.1f}s)" if mins > 0 else f"{elapsed_t:.1f}s"
        print("\n--- RIASSUNTO ENGEL & VÖLKERS ---")
        print(f"Data Esecuzione    : {TODAY}")
        print(f"Nuovi immobili     : {new_added}")
        print(f"Variazioni prezzo  : {price_vars}")
        print(f"Non più visibili   : {not_visible}")
        print(f"Datalake aggiornato: {DATALAKE_PATH}")
        print(f"Tempo impiegato    : {dur_str}")
        print("---------------------------------")
