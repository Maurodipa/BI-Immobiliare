import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    if 'ges' in d.get('titolo', '').lower() and d.get('stato_annuncio') == 'Attivo':
        print(f"Titolo: {d.get('titolo')}")
        print(f"Portali: {d.get('url_sorgenti')}")
        print(f"Prezzo attuale: {d.get('prezzo_attuale')}")
        print(f"Storico:")
        for s in d.get('storico_prezzi', []):
            print(f"   {s}")
