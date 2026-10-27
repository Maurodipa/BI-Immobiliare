import json

scarti_urls = [
    "124908953",
    "118544591",
    "30573194",
    "131373900",
    "127295515",
    "35066504"
]

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scartati_count = 0
for d in data:
    for url in d.get('url_sorgenti', []):
        if any(scarto_id in url for scarto_id in scarti_urls):
            if d.get('stato_annuncio') != 'Scartato':
                d['stato_annuncio'] = 'Scartato'
                scartati_count += 1
                print(f"Scartato: {d.get('titolo')}")
            break

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale nuovi scartati: {scartati_count}")
