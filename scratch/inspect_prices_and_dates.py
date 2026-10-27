import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== ANNUNCI CON VARIAZIONE DI PREZZO ===')
var_count = 0
for d in data:
    sp = d.get('storico_prezzi', [])
    if len(sp) > 1:
        # Check if actual price changed
        prices = [x.get('prezzo') for x in sp]
        if len(set(prices)) > 1:
            var_count += 1
            print(f"[{d.get('stato_annuncio')}] {d.get('titolo')} (Piano: {d.get('piano')})")
            for s in sp:
                p = s.get('prezzo', 0)
                dt = s.get('data_rilevazione', '')
                print(f"   * {dt}: € {p:,}")
print(f"\nTotale annunci con variazioni effettive di prezzo: {var_count}\n")

print('=== DATE DI SCOPERTA (date_market_research[0]) ===')
discovery_dates = {}
for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        d0 = d.get('date_market_research', [''])[0]
        discovery_dates.setdefault(d0, []).append(d.get('titolo'))

for dt, items in sorted(discovery_dates.items()):
    print(f"Data {dt}: {len(items)} annunci attivi")
    for it in items[:3]:
        print(f"   - {it}")
