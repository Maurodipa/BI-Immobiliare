import json
import re

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count_aste = 0
count_floor = 0

def is_asta(titolo, url_sorgenti):
    t = titolo.lower()
    return 'asta' in t or 'nuda propriet' in t or any('asta' in u for u in url_sorgenti)

def is_low_floor(piano_str):
    if not piano_str: return False
    p = str(piano_str).upper()
    
    # Exclude Ground/Mezzanine/Basement
    if any(x in p for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO', ' S', ' T', ' R']):
        return True
    if p in ['T', 'S', 'R', 'S1', 'S2']:
        return True
        
    # Exclude 1st floor
    # look for '1', '1º', '1°' (but not 10, 11 etc)
    if re.search(r'\b1(?!\d)', p) or '1º' in p or '1°' in p:
        # ensure it's not "10" "11" "12"
        return True
        
    return False

for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        # Check Asta
        if is_asta(d.get('titolo', ''), d.get('url_sorgenti', [])):
            d['stato_annuncio'] = 'Scartato'
            count_aste += 1
            print(f"Scartata asta: {d.get('titolo')}")
            continue
            
        # Check Floor
        if is_low_floor(d.get('piano', '')):
            d['stato_annuncio'] = 'Scartato'
            count_floor += 1
            print(f"Scartato piano basso ({d.get('piano')}): {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Aste scartate: {count_aste}")
print(f"Piani bassi scartati: {count_floor}")
