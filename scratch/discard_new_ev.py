import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for d in data:
    t = d.get('titolo', '').lower()
    if 'villaggio azzurro' in t:
        d['stato_annuncio'] = 'Scartato'
        count += 1
        print(f"Scartato: {d.get('titolo')} (motivo: fuori poligono Spinaceto)")
    elif 'sant\'onofrio' in t:
        d['stato_annuncio'] = 'Scartato'
        count += 1
        print(f"Scartato: {d.get('titolo')} (motivo: piano 1 e fuori poligono Trastevere)")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale aggiornati a Scartato: {count}")
