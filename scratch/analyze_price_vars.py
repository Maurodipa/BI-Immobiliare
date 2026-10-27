import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Totale immobili nel datalake: {len(data)}")

ribassi = []
discrepanze = []

for d in data:
    if d.get('stato_annuncio') == 'Scartato':
        continue
    titolo = d.get('titolo', '')
    storico = d.get('storico_prezzi', [])
    prezzi_multipli = sorted(list(d.get('prezzi_multipli', {d.get('prezzo_attuale', 0)})))
    
    # 1. Storico date
    if storico and len(storico) >= 2:
        by_date = {}
        for s in storico:
            dt = s.get('data_rilevazione', '')
            p = s.get('prezzo', 0)
            if dt and p > 0:
                by_date.setdefault(dt, []).append(p)
        dates = sorted(by_date.keys())
        if len(dates) >= 2:
            first_p = by_date[dates[0]][0]
            last_p = by_date[dates[-1]][-1]
            if first_p != last_p:
                diff = last_p - first_p
                pct = (diff / first_p) * 100
                ribassi.append({
                    'titolo': titolo,
                    'zona': d.get('indirizzo_zona', ''),
                    'first_date': dates[0],
                    'last_date': dates[-1],
                    'first_p': first_p,
                    'last_p': last_p,
                    'diff': diff,
                    'pct': pct,
                    'urls': d.get('url_sorgenti', []),
                    'portale': d.get('nome_portale', '')
                })

    # 2. Prezzi multipli (discrepanze tra portali / annunci dello stesso immobile)
    if len(prezzi_multipli) > 1 and max(prezzi_multipli) > min(prezzi_multipli):
        delta = max(prezzi_multipli) - min(prezzi_multipli)
        discrepanze.append({
            'titolo': titolo,
            'zona': d.get('indirizzo_zona', ''),
            'prezzi': prezzi_multipli,
            'delta': delta,
            'urls': d.get('url_sorgenti', [])
        })

print(f"\n--- VARIAZIONI DI PREZZO NEL TEMPO (RIBASSI / AUMENTI) ({len(ribassi)}) ---")
for r in ribassi:
    print(f"- {r['titolo'][:50]} ({r['zona']}): € {r['first_p']:,} -> € {r['last_p']:,} ({r['diff']:+,} / {r['pct']:+.1f}%) [dal {r['first_date']} al {r['last_date']}]")

print(f"\n--- DISCREPANZE DI PREZZO TRA PORTALI / ANNUNCI ({len(discrepanze)}) ---")
for disc in discrepanze:
    print(f"- {disc['titolo'][:50]} ({disc['zona']}): {disc['prezzi']} (Delta: € {disc['delta']:,})")
