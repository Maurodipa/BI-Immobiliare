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
    "trevignano", "bracciano", "fiumicino", "ciampino", "frascati", "pomezia", "guidonia",
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
    """Estrae appartamenti da una pagina E&V analizzando gli elementi <article> nel DOM.
    
    Returns:
        tuple: (raw_count, valid_results)
    """
    soup = BeautifulSoup(src, "html.parser")
    articles = soup.find_all("article")
    raw_count = len(articles)
    
    if not articles:
        return 0, []

    results = []
    for a in articles:
        # Link annuncio
        link_tag = a.find("a", href=re.compile(r'/exposes/|/proprieta/'))
        if not link_tag:
            continue
        url = link_tag.get('href', '')
        if not url.startswith('http'):
            url = f"https://www.engelvoelkers.com{url}"

        # Location / Indirizzo (es: "Quartiere XXV Appio Claudio, Roma, Lazio, Italia")
        loc_p = a.find("p", class_=re.compile(r'_location_'))
        loc_str = loc_p.get_text(strip=True) if loc_p else ""
        
        # Filtro citta: solo Roma
        if "roma" not in loc_str.lower():
            continue

        # Estrai nome quartiere/zona
        parts = [p.strip() for p in loc_str.split(',') if p.strip()]
        zona = parts[0] if parts else "Roma"

        # Prezzo
        price_tag = a.find(attrs={"data-testid": "search-components_result-card_price"})
        price = 0
        if price_tag:
            p_clean = re.sub(r'[^\d]', '', price_tag.get_text())
            price = int(p_clean) if p_clean else 0
        if price == 0 or price > PREZZO_MAX:
            continue

        # Locali / Stanze
        rooms_tag = a.find(attrs={"data-testid": re.compile(r'-rooms$')})
        rooms = 0
        if rooms_tag:
            m = re.search(r'(\d+)', rooms_tag.get_text())
            rooms = int(m.group(1)) if m else 0
        if rooms < LOCALI_MIN:
            continue

        # Superficie / Area
        area_tag = a.find(attrs={"data-testid": re.compile(r'-livingArea$')})
        area = 0
        if area_tag:
            m = re.search(r'(\d+)', area_tag.get_text())
            area = int(m.group(1)) if m else 0

        # Titolo / Headline
        h2 = a.find("h2", attrs={"data-testid": "search-components_result-card_headline"}) or a.find("h2")
        title = h2.get_text(strip=True) if h2 else "Appartamento"
        title = title.replace("\ufffd", "'").strip()

        # Filtro zona: lista verde / lista rossa
        if not zone_ammessa(zona):
            print(f"   [EV] Escluso (zona fuori area): {zona} | {title[:40]}")
            continue

        # Controllo avanzato con Geocoding se la zona e generica e non verificata verde
        is_green = any(parola in zona.lower() for parola in ZONE_VERDI)
        if not is_green:
            if not geocode_and_check(title):
                print(f"   [EV] Escluso (geocoding fuori poligono): {title[:60]}")
                continue

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

    return raw_count, results


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

                    stanze_ext = int(ext.get('numero_stanze') or 0)
                    stanze_apt = int(apt.get('numero_stanze') or 0)
                    stesse_stanze = (stanze_ext == stanze_apt) or (
                        abs(stanze_ext - stanze_apt) <= 1 and 
                        ext.get('prezzo_attuale') == apt.get('prezzo_attuale') and 
                        (ext.get('prezzo_attuale') or 0) > 0
                    )

                    if (stessa_via and
                        ext.get('zona') == apt.get('zona') and
                        stesse_stanze and
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
    """Naviga E&V pagina per pagina tramite click sul pulsante 'Avanti'.
    
    Estrae le card direttamente dagli elementi <article> renderizzati nel DOM
    a ciascuna pagina e gestisce il banner dei cookie Didomi.
    
    Returns:
        tuple: (new_apts, pages_scanned, raw_total)
    """
    print("1. Inizializzazione browser stealth (Engel & Völkers)...")
    new_apts = []
    pages_scanned = 0
    raw_total = 0

    # Selettore CSS del bottone "pagina successiva" di E&V
    NEXT_BTN = '[data-testid="pagination-arrow-next"]'
    NEXT_DISABLED_CLASS = "WW14wa_arrowDisabled"

    with SB(uc=True, headless=False) as sb:
        print("2. CONNESSIONE RIUSCITA!")
        print("3. Navigazione pagina 1...")
        sb.uc_open_with_reconnect(BASE_URL, 6)
        time.sleep(4)

        # Gestione consenso cookie Didomi (se presente)
        try:
            sb.click('button#didomi-notice-agree-button', timeout=4)
            print("   - Banner cookie Didomi accettato.")
            time.sleep(1)
        except Exception:
            pass

        for page in range(1, MAX_PAGES + 1):
            # Scrolla fino in fondo per attivare il lazy loading di tutte le card e paginazione
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            src = sb.get_page_source()
            raw_count, page_apts = extract_cards_ev(src)

            # Se la pagina non contiene nessun elemento annuncio -> fine reale
            if raw_count == 0:
                print(f"   - Pagina {page}: 0 annunci rilevati nel DOM. Fine paginazione.")
                break

            raw_total += raw_count
            pages_scanned += 1
            new_apts.extend(page_apts)
            print(f"   - Pagina {page}: {raw_count} grezzi -> {len(page_apts)} validi (tot. validi: {len(new_apts)})")

            # Se abbiamo raggiunto il numero massimo di pagine
            if page >= MAX_PAGES:
                print(f"   - Raggiunto il limite massimo di {MAX_PAGES} pagine.")
                break

            # Verifica presenza del pulsante 'Avanti'
            if not sb.is_element_present(NEXT_BTN):
                time.sleep(2)
                if not sb.is_element_present(NEXT_BTN):
                    print(f"   - Pulsante 'Avanti' non presente. Fine paginazione a pagina {page}.")
                    break

            try:
                next_btn = sb.find_element(NEXT_BTN)
                btn_classes = next_btn.get_attribute("class") or ""
                if NEXT_DISABLED_CLASS in btn_classes or not next_btn.is_enabled():
                    print(f"   - Pulsante 'Avanti' disabilitato. Fine paginazione a pagina {page}.")
                    break
            except Exception as ex:
                print(f"   - Errore lettura stato bottone: {ex}. Fine paginazione.")
                break

            # Navigazione alla pagina successiva via JavaScript click
            print(f"   - Navigazione pagina {page + 1}...")
            try:
                sb.js_click(NEXT_BTN)
                time.sleep(4)
            except Exception as e:
                print(f"   - Errore click Next: {e}. Fine paginazione.")
                break

    return new_apts, pages_scanned, raw_total


SCAN_STATS_PATH = "scan_stats_ev.json"


if __name__ == "__main__":
    start_t = time.time()
    new_apts, pages_scanned, raw_total = scrape()

    elapsed_t = time.time() - start_t
    mins, secs = divmod(elapsed_t, 60)
    dur_str = f"{int(mins)}m {secs:04.1f}s ({elapsed_t:.1f}s)" if mins > 0 else f"{elapsed_t:.1f}s"

    if not new_apts:
        print(f"\nNessun annuncio estratto da Engel & Völkers dopo {pages_scanned} pagine ({raw_total} grezzi).")
        new_added, price_vars, not_visible = 0, 0, 0
    else:
        new_added, price_vars, not_visible = process_datalake(new_apts)

    # Salva statistiche scansione per run_all_scanners.py e dump_table_v4.py
    scan_stats = {
        "portale": "Engel & Völkers",
        "data": TODAY,
        "pagine_scansionate": pages_scanned,
        "annunci_grezzi": raw_total,
        "annunci_validi": len(new_apts),
        "nuovi_aggiunti": new_added,
        "variazioni_prezzo": price_vars,
        "non_piu_visibili": not_visible,
        "durata_secondi": round(elapsed_t, 1),
    }
    with open(SCAN_STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(scan_stats, f, indent=2, ensure_ascii=False)

    print("\n--- RIASSUNTO ENGEL & VÖLKERS ---")
    print(f"Data Esecuzione    : {TODAY}")
    print(f"Pagine scansionate : {pages_scanned}")
    print(f"Annunci grezzi     : {raw_total}")
    print(f"Annunci validi     : {len(new_apts)}")
    print(f"Nuovi immobili     : {new_added}")
    print(f"Variazioni prezzo  : {price_vars}")
    print(f"Non più visibili   : {not_visible}")
    print(f"Datalake aggiornato: {DATALAKE_PATH}")
    print(f"Tempo impiegato    : {dur_str}")
    print("---------------------------------")
