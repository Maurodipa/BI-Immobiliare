import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_price_variation(item):
    storico = item.get('storico_prezzi', [])
    if not storico or len(storico) < 2:
        return "-"
    
    # Collect price progression across distinct dates
    by_date = {}
    for s in storico:
        dt = s.get('data_rilevazione', '')
        p = s.get('prezzo', 0)
        if dt and p > 0:
            by_date.setdefault(dt, []).append(p)
            
    dates = sorted(by_date.keys())
    if len(dates) < 2:
        return "-"
        
    first_date = dates[0]
    last_date = dates[-1]
    
    # If the set of prices on first date equals the set of prices on last date (e.g. multi-portal dual pricing), no real trend
    if set(by_date[first_date]) == set(by_date[last_date]):
        return "-"
        
    p_initial = by_date[first_date][0]
    p_current = by_date[last_date][-1]
    
    diff = p_current - p_initial
    if diff == 0:
        return "-"
        
    pct = (diff / p_initial) * 100
    diff_abs = f"{abs(diff):,}".replace(',', '.')
    
    if diff < 0:
        return f"📉 -€ {diff_abs} ({pct:.1f}%)"
    elif diff > 0:
        return f"📈 +€ {diff_abs} (+{pct:.1f}%)"
    return "-"

print("=== RISULTATO VARIAZIONI DI PREZZO NEL DATALAKE ===")
for d in data:
    v = get_price_variation(d)
    if v != "-":
        t = d.get('titolo', '')[:45]
        st = d.get('stato_annuncio')
        p_cur = d.get('prezzo_attuale')
        print(f"[{st}] {t} | Attuale: {p_cur} | {v.encode('ascii', 'replace').decode()}")
