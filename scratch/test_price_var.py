import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_price_variation(item):
    storico = item.get('storico_prezzi', [])
    if not storico or len(storico) < 2:
        return "-"
    
    # Filter unique consecutive prices
    filtered = []
    for s in storico:
        p = s.get('prezzo', 0)
        dt = s.get('data_rilevazione', '')
        if p > 0:
            if not filtered or filtered[-1]['prezzo'] != p:
                filtered.append({'prezzo': p, 'data': dt})
                
    if len(filtered) < 2:
        return "-"
        
    p_first = filtered[0]['prezzo']
    p_last = filtered[-1]['prezzo']
    diff = p_last - p_first
    
    if diff == 0:
        return "-"
        
    pct = (diff / p_first) * 100
    
    p_first_fmt = f"{p_first:,}".replace(',', '.')
    diff_abs_fmt = f"{abs(diff):,}".replace(',', '.')
    
    if diff < 0:
        return f"📉 -€ {diff_abs_fmt} ({pct:.1f}%) [da € {p_first_fmt}]"
    else:
        return f"📈 +€ {diff_abs_fmt} (+{pct:.1f}%) [da € {p_first_fmt}]"

for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        var = get_price_variation(d)
        if var != "-":
            print(f"{d.get('titolo')[:40]} | Var: {var.encode('ascii', 'replace').decode()}")
