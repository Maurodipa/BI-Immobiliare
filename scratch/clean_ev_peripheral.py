import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scartati_count = 0
for d in data:
    t = d.get('titolo', '').lower()
    z = d.get('indirizzo_zona', '').lower()
    urls = [u.lower() for u in d.get('url_sorgenti', [])]
    
    # Check if out of zone (Della Vittoria, Primavalle, Gemelli) or specific IDs
    is_out = any(k in t or k in z for k in ['della vittoria', 'delle vittorie', 'primavalle', 'gemelli', 'w-04bzu3', 'w-04buwa', 'w-04bk64'])
    is_out = is_out or any(any(x in u for x in ['w-04bzu3', 'w-04buwa', 'w-04bk64']) for u in urls)
    
    if is_out and d.get('stato_annuncio') != 'Scartato':
        d['stato_annuncio'] = 'Scartato'
        scartati_count += 1
        print(f"Scartato: {d.get('titolo')} ({d.get('indirizzo_zona')})")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale scartati: {scartati_count}")
