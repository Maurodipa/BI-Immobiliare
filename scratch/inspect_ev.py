import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    for u in d.get('url_sorgenti', []):
        if 'engel' in u.lower():
            print(f"Titolo: {d.get('titolo')}")
            print(f"URL: {u}")
            print(f"Stato: {d.get('stato_annuncio')}")
            print(f"Prezzo: {d.get('prezzo_attuale')}")
            print("-" * 40)
