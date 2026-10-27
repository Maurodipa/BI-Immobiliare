import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for d in data:
    clean_history = []
    for s in d.get('storico_prezzi', []):
        p = s.get('prezzo', 0)
        if p > 10_000_000:
            count += 1
            print(f"Cleaning {d.get('titolo')[:40]}: {p}")
        else:
            clean_history.append(s)
    
    # Se la cronologia e vuota dopo la pulizia, inseriamo il prezzo attuale
    if not clean_history:
        clean_history = [{'prezzo': d.get('prezzo_attuale', 0), 'data_rilevazione': d.get('date_market_research', ['2026-10-20'])[-1]}]
    d['storico_prezzi'] = clean_history

print(f"Total cleaned anomalous price records: {count}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
