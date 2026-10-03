import json
import re
import requests
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

POLYGON = "41.90151,12.469482;41.900999,12.464333;41.899338,12.463818;41.894994,12.467766;41.891799,12.472057;41.890777,12.47901;41.892758,12.481842;41.895377,12.482786;41.896655,12.486477;41.898188,12.490211;41.900297,12.492571;41.902149,12.490854;41.903108,12.488923;41.90413,12.487507;41.905982,12.48313;41.911763,12.477207;41.910741,12.472959;41.905599,12.475147;41.90151,12.469482"

def is_point_in_polygon(lat, lon, polygon_str):
    coords = []
    for pair in polygon_str.split(';'):
        if pair.strip():
            lat_p, lon_p = map(float, pair.split(','))
            coords.append((lat_p, lon_p))
            
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

def extract_query(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico)\s+([^,-]+)', title, re.IGNORECASE)
    if match: return match.group(0).strip()
    match = re.search(r' a ([A-Z][a-zA-Z\s]+)', title)
    if match: return match.group(1).strip()
    match = re.search(r'in zona ([A-Z][a-zA-Z\s]+)', title)
    if match: return match.group(1).strip()
    return None

def geocode_and_check(title):
    q = extract_query(title)
    if not q: return True # If we can't extract, assume inside to be safe
    
    headers = {'User-Agent': 'BI_Immobiliare_Agent/1.0'}
    url = f"https://nominatim.openstreetmap.org/search?q={q}, Roma&format=json&limit=1"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        data = r.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return is_point_in_polygon(lat, lon, POLYGON)
    except:
        pass
    return True

DATALAKE_PATH = "datalake_poligono.json"
data = json.load(open(DATALAKE_PATH, encoding="utf-8"))

rimasti = []
rimossi = []

for d in data:
    if d.get("nome_portale") == "engelvoelkers.com" and d.get("stato_annuncio") == "Attivo":
        if not geocode_and_check(d.get("titolo", "")):
            rimossi.append(d)
            print(f"RIMOSSO (fuori poligono): {d.get('titolo')}")
            continue
    rimasti.append(d)

with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
    json.dump(rimasti, f, indent=4, ensure_ascii=False)
