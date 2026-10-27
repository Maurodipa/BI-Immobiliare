import json
data = json.load(open('datalake_poligono.json', encoding='utf-8'))
for d in data:
    if d.get('stato_annuncio') == 'Attivo' and d.get('nome_portale') == 'immobiliare.it':
        print(d.get('titolo'), d.get('date_market_research'))
