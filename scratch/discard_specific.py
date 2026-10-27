import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for d in data:
    urls = d.get('url_sorgenti', [])
    if any('116372013' in url for url in urls):
        if d.get('stato_annuncio') != 'Scartato':
            d['stato_annuncio'] = 'Scartato'
            count += 1
            print(f"Scartato: {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale scartati: {count}")
