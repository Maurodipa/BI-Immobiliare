import json

with open('datalake_poligono.json', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    if 'scrofa' in d.get('titolo', '').lower():
        print(f"FOUND: {d.get('titolo')}")
        d['stato_annuncio'] = 'Scartato'

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
