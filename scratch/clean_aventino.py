import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    t = d.get('titolo', '').lower()
    z = d.get('indirizzo_zona', '').lower()
    if 'fonte di fauno' in t or 'aventino' in t or 'aventino' in z:
        if d.get('stato_annuncio') != 'Scartato':
            d['stato_annuncio'] = 'Scartato'
            print(f"Scartato fuori poligono: {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
