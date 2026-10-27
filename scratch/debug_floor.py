import json
import re

def is_low_floor_fixed(piano_str):
    if not piano_str: return False
    p = str(piano_str).upper()
    if any(x in p for x in ['TERRA', 'RIALZATO', 'SEMINTERRATO']): return 'TERRA/RIALZ/SEMIN in p'
    p_exact = p.strip()
    if p_exact in ['T', 'S', 'R', 'S1', 'S2', '1']: return 'exact match T/S/R/1'
    if re.search(r'\b1\b(?!0|1|2|3|4|5|6|7|8|9)', p): return 'regex 1'
    if '1º' in p or '1°' in p or '1' in p: return '1 in p'
    return False

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    p = d.get('piano', '')
    res = is_low_floor_fixed(p)
    if res and d.get('stato_annuncio') == 'Scartato':
        print(f"{res} -> {p} ({d.get('titolo')})")
