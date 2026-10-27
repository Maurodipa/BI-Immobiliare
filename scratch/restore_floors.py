import json
import re

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def is_low_floor_fixed(piano_str):
    if not piano_str: return False
    p = str(piano_str).upper()
    
    if any(x in p for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO']):
        return True
    
    # Exact match for T, S, R, S1, S2, 1
    p_exact = p.strip()
    if p_exact in ['T', 'S', 'R', 'S1', 'S2', '1']:
        return True
        
    # Regex to catch '1º', '1°', '1', 'Piano 1' but not '10', '11'
    if re.search(r'\b1\b(?!0|1|2|3|4|5|6|7|8|9)', p):
        return True
    if '1º' in p or '1°' in p or '1' in p:
        return True
        
    return False

restored = 0
for d in data:
    if d.get('stato_annuncio') == 'Scartato':
        p = d.get('piano', '')
        # Only restore if it was a floor mistaken for ' S' (like '4º SENZA ASCENSORE')
        # AND it's NOT actually a low floor
        if p and not is_low_floor_fixed(p):
            # Check if it was discarded because of ASTA
            t = d.get('titolo', '').lower()
            url_sorgenti = [u.lower() for u in d.get('url_sorgenti', [])]
            is_asta = 'asta' in t or 'nuda propriet' in t or any('asta' in u for u in url_sorgenti)
            if not is_asta:
                # Also check if it's one of the URLs to discard!
                # We can just run the url discard again later
                d['stato_annuncio'] = 'Attivo'
                restored += 1
                print(f"Ripristinato: {p} - {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Ripristinati: {restored}")
