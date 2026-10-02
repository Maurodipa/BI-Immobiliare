import json

with open('datalake_roma.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    if item.get('prezzo_attuale', 0) > 10_000_000:
        item['prezzo_attuale'] = item['prezzo_attuale'] // 100
    
    for storico in item.get('storico_prezzi', []):
        if storico.get('prezzo', 0) > 10_000_000:
            storico['prezzo'] = storico['prezzo'] // 100

with open('datalake_roma.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
