import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

today_items = [d for d in data if d.get('date_market_research') and d.get('date_market_research')[0] == '2026-10-19']
print(f"Total new items discovered today: {len(today_items)}")
for d in today_items:
    p = d.get('prezzo_attuale', 0)
    p_fmt = f"{p:,}".replace(',', '.')
    print(f"[{d.get('nome_portale')}] {d.get('titolo')} | € {p_fmt} | Piano: {d.get('piano')} | Zona: {d.get('indirizzo_zona')}")
