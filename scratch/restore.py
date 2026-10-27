import json
data = json.load(open('datalake_poligono.json', encoding='utf-8'))
for d in data:
    t = d.get('titolo', '')
    if 'Del Gesù' in t or "Sant'ambrogio" in t or 'Beato Angelico' in t:
        d['stato_annuncio'] = 'Attivo'
with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
