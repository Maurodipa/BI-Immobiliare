import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_price_variation(item):
    storico = item.get('storico_prezzi', [])
    prezzi_multipli = sorted(list(item.get('prezzi_multipli', {item.get('prezzo_attuale', 0)})))
    
    # 1. Check historical price change over time
    if storico and len(storico) >= 2:
        by_date = {}
        for s in storico:
            dt = s.get('data_rilevazione', '')
            p = s.get('prezzo', 0)
            if dt and p > 0:
                by_date.setdefault(dt, []).append(p)
                
        dates = sorted(by_date.keys())
        if len(dates) >= 2:
            first_date = dates[0]
            last_date = dates[-1]
            
            # Check if prices differ across time
            if set(by_date[first_date]) != set(by_date[last_date]):
                p_initial = by_date[first_date][0]
                p_current = by_date[last_date][-1]
                diff = p_current - p_initial
                if diff != 0:
                    pct = (diff / p_initial) * 100
                    diff_abs = f"{abs(diff):,}".replace(',', '.')
                    p_init_fmt = f"{p_initial:,}".replace(',', '.')
                    if diff < 0:
                        return f"📉 -€ {diff_abs} (-{abs(pct):.1f}%) da € {p_init_fmt}"
                    else:
                        return f"📈 +€ {diff_abs} (+{pct:.1f}%) da € {p_init_fmt}"
                        
    # 2. Check portal price difference (if multiple prices currently)
    if len(prezzi_multipli) > 1 and all(p > 0 for p in prezzi_multipli):
        delta = max(prezzi_multipli) - min(prezzi_multipli)
        delta_fmt = f"{delta:,}".replace(',', '.')
        return f"⚖️ Δ € {delta_fmt} tra portali"
        
    return "-"

for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        # fake prezzi_multipli if not deduplicated yet
        d_copy = d.copy()
        d_copy['prezzi_multipli'] = {d.get('prezzo_attuale', 0)}
        v = get_price_variation(d_copy)
        if v != "-":
            print(f"{d.get('titolo')[:40]} | Prezzo: {d.get('prezzo_attuale')} | {v.encode('ascii', 'replace').decode()}")
