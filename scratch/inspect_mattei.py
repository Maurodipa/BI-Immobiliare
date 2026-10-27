import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, d in enumerate(data):
    if 'mattei' in d.get('titolo', '').lower() and d.get('stato_annuncio') == 'Attivo':
        print(f"ID {i}: {d.get('titolo')}")
        print(f"  Stato: {d.get('stato_annuncio')}")
        print(f"  Prezzo: {d.get('prezzo_attuale')}")
        print(f"  Date: {d.get('date_market_research')}")
        print(f"  URLs: {d.get('url_sorgenti')}\n")
