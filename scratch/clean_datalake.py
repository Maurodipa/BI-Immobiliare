import json
import re

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Hard filters
ZONE_ROSSE = [
    "torrino",
    "parioli", "flaminio", "prati", "delle vittorie", "borgo", "aurelio", 
    "trionfale", "testaccio", "aventino", "san saba", "esquilino", 
    "celio", "macao", "castro pretorio", "ludovisi", "sallustiano",
    "termini", "turati"
]

URLS_TO_DISCARD = [
    '131338830', '124762811', '130243626', '130614394', '114263601',
    '36695872', '35854570', '34821519', '30907780', '124657859',
    '34149735', '36814943', '32803453', '35805958', '35854570',
    '132501986', '11876600', '31325965', '35614310', '33798813',
    '133241538', '36041974', '04buwa', '36672902', '35907573',
    '35405090', '29016911', '36665036', '34969851', '36041974',
    '34385063', '34755432', '116372013', '133412520'
]

def is_asta(titolo, url_sorgenti):
    t = titolo.lower()
    return 'asta' in t or 'nuda propriet' in t or any('asta' in u for u in url_sorgenti)

def is_low_floor(piano_str):
    if not piano_str: return False
    p = str(piano_str).upper()
    
    if any(x in p for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO']):
        return True
    
    p_exact = p.strip()
    if p_exact in ['T', 'S', 'R', 'S1', 'S2', '1']:
        return True
        
    if re.search(r'\b1\b(?!0|1|2|3|4|5|6|7|8|9)', p):
        return True
    if '1º' in p or '1°' in p or '1\ufffd' in p:
        return True
        
    return False

# First, restore all currently "Scartati" to Attivo, except those that were naturally dead
for d in data:
    if d.get('stato_annuncio') == 'Scartato':
        d['stato_annuncio'] = 'Attivo'

# Now apply all filters strictly
scartati = 0
for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        t = d.get('titolo', '').lower()
        z = d.get('indirizzo_zona', '').lower()
        
        # 1. URL discard
        urls = d.get('url_sorgenti', [])
        if any(discard_id in url for discard_id in URLS_TO_DISCARD for url in urls):
            d['stato_annuncio'] = 'Scartato'
            scartati += 1
            continue
            
        # 2. Zone Rosse / Icilio / Gemelli
        if any(zr in t or zr in z for zr in ZONE_ROSSE) or 'icilio' in t or 'gemelli' in t:
            d['stato_annuncio'] = 'Scartato'
            scartati += 1
            continue
            
        # 3. Piani bassi (T, S, R, 1) per appartamenti normali
        t_upper = t.upper()
        is_c1_c2 = any(x in t_upper for x in ["C1", "C2", "C/1", "C/2", "NEGOZIO", "MAGAZZINO", "OPEN SPACE", "LOFT", "UFFICIO", "STUDIO"])
        is_asta_item = "ASTA" in t_upper or "NUDA PROPRIET" in t_upper or any("ASTA" in u.upper() for u in urls)
        
        if not is_c1_c2 and not is_asta_item:
            if is_low_floor(d.get('piano', '')):
                d['stato_annuncio'] = 'Scartato'
                scartati += 1
                continue

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Pulizia completa: {scartati} annunci scartati in totale.")
