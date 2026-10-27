import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for d in data:
    t = d.get('titolo', '').lower()
    z = d.get('indirizzo_zona', '').lower()
    
    if 'torrino' in t or 'torrino' in z:
        if d.get('stato_annuncio') != 'Scartato':
            d['stato_annuncio'] = 'Scartato'
            count += 1
            print(f"Scartato: {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale annunci al Torrino scartati: {count}")
