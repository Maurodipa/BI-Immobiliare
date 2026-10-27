import json
data = json.load(open('datalake_poligono.json', encoding='utf-8'))
found = False
for d in data:
    t = d.get('titolo', '').lower()
    z = d.get('indirizzo_zona', '').lower()
    if 'palombara' in t or 'palombara' in z or 'sabina' in t or 'sabina' in z:
        print(f"Trovato e scartato: {d.get('titolo')}")
        d['stato_annuncio'] = 'Scartato'
        found = True

if found:
    with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
