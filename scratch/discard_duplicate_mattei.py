import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    urls = d.get('url_sorgenti', [])
    if any('133412520' in url for url in urls):
        d['stato_annuncio'] = 'Scartato'
        print(f"Scartato duplicato asta: {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
