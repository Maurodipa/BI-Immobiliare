import json, requests, sys
sys.path.append('.')
from scrape_ev import is_point_in_polygon, POLYGON

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

today_items = [d for d in data if d.get('date_market_research') and d.get('date_market_research')[0] == '2026-10-19']

for d in today_items:
    t = d.get('titolo', '')
    query = t.split(',')[0].replace('Bilocale in ', '').replace('Trilocale in ', '').replace('Quadrilocale in ', '').replace('Appartamento in ', '').replace('Attico in ', '').replace('Villa in ', '').strip()
    url = f"https://nominatim.openstreetmap.org/search?q={query}, Roma&format=json&limit=1"
    try:
        r = requests.get(url, headers={'User-Agent': 'test'}, verify=False, timeout=3)
        res = r.json()
        if res:
            lat, lon = float(res[0]['lat']), float(res[0]['lon'])
            inside = is_point_in_polygon(lat, lon, POLYGON)
            print(f"[{'IN' if inside else 'OUT'}] {t[:40]} -> {res[0].get('display_name')[:50]}")
        else:
            print(f"[???] {t[:40]} -> No geocode")
    except Exception as e:
        print(f"[ERR] {t[:40]}: {e}")
