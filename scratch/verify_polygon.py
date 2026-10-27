import json, re, requests, urllib3, time
urllib3.disable_warnings()

POLYGON = '41.90151,12.469482;41.900999,12.464333;41.899338,12.463818;41.894994,12.467766;41.891799,12.472057;41.890777,12.47901;41.892758,12.481842;41.895377,12.482786;41.896655,12.486477;41.898188,12.490211;41.900297,12.492571;41.902149,12.490854;41.903108,12.488923;41.90413,12.487507;41.905982,12.48313;41.911763,12.477207;41.910741,12.472959;41.905599,12.475147;41.90151,12.469482'

def is_point_in_polygon(lat, lon, polygon_str):
    coords = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in polygon_str.split(';') if p.strip()]
    x, y = lon, lat
    n = len(coords)
    inside = False
    p1x, p1y = coords[0][1], coords[0][0]
    for i in range(n + 1):
        p2x, p2y = coords[i % n][1], coords[i % n][0]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def extract_street(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico|arco)\s+([^,]+)', title, re.IGNORECASE)
    if match:
        street = match.group(0).strip()
        street = re.sub(r'\s+s\.n\.c|\s+\d+.*$', '', street, flags=re.IGNORECASE).strip()
        return street
    return ''

def geocode(title):
    q = extract_street(title)
    if not q:
        return None, None, None
    headers = {'User-Agent': 'BI_Immobiliare_Agent/1.0'}
    url = f'https://nominatim.openstreetmap.org/search?q={q}, Roma, Italia&format=json&limit=1'
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=7)
        data = r.json()
        if data:
            lat, lon = float(data[0]['lat']), float(data[0]['lon'])
            return lat, lon, q
    except Exception:
        pass
    return None, None, q

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

active = [d for d in data if d.get('stato_annuncio') == 'Attivo']
print(f"Totale annunci attivi da verificare: {len(active)}\n")

print(f"{'#':<4} {'Via estratta':<35} {'Lat':<12} {'Lon':<12} {'Nel poligono?':<15} Titolo")
print("-" * 120)

fuori = []
no_geocode = []

for i, apt in enumerate(active, 1):
    title = apt.get('titolo', '')
    time.sleep(1.1)  # rispetta rate limit Nominatim (max 1 req/s)
    lat, lon, via = geocode(title)

    if lat is None:
        no_geocode.append((i, title[:60], via or 'N/A'))
        print(f"{i:<4} {'(nessuna via nel titolo)':<35} {'N/A':<12} {'N/A':<12} {'SKIP':<15} {title[:60]}")
        continue

    # Sanity check: scarta risultati fuori dalla provincia di Roma (coord assurde)
    # Roma è circa: lat 41.6-42.1, lon 12.2-12.8
    if not (41.5 < lat < 42.2 and 12.1 < lon < 13.0):
        print(f"{i:<4} {(via or '')[:35]:<35} {lat:<12.5f} {lon:<12.5f} {'FALSO (fuori IT)':<15} {title[:60]}")
        no_geocode.append((i, title[:60], via or '?'))
        continue

    in_poly = is_point_in_polygon(lat, lon, POLYGON)
    stato = "[ SI ]" if in_poly else "[ NO ]"
    print(f"{i:<4} {(via or '')[:35]:<35} {lat:<12.5f} {lon:<12.5f} {stato:<15} {title[:60]}")

    if not in_poly:
        fuori.append((i, title[:60], via, lat, lon))

print("\n" + "="*80)
if fuori:
    print(f"\n*** ANNUNCI POTENZIALMENTE FUORI POLIGONO ({len(fuori)}) ***")
    for i, t, via, lat, lon in fuori:
        print(f"  #{i}: {t}")
        print(f"      Via: {via} | Coords: {lat:.5f}, {lon:.5f}")
        print(f"      Maps: https://www.google.com/maps?q={lat},{lon}")
else:
    print("\n[OK] Tutti gli annunci sembrano essere nel poligono!")

if no_geocode:
    print(f"\n[SKIP] ANNUNCI SENZA GEOCODING ({len(no_geocode)}) -- verifica manuale consigliata:")
    for i, t, via in no_geocode:
        print(f"  #{i}: {t}")
