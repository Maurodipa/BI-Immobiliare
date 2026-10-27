import requests
import urllib3
urllib3.disable_warnings()

queries = [
    'Ponte Palatino, Roma',
    'Via della Lungara, Roma',
    'Via delle Mantellate, Roma',
    'Via dei Riari, Roma',
    'Giardino Domenico Bonamini, Roma',
    'Via della Luce, Roma',
    'Via Anicia, Roma',
    'Piazza in Piscinula, Roma',
    'Ponte Sisto, Roma',
    'Ponte Mazzini, Roma',
    'Gran Farina, Roma'
]

for q in queries:
    try:
        r = requests.get(f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1', headers={'User-Agent': 'test'}, verify=False, timeout=5)
        d = r.json()
        if d:
            print(f"{q:35} -> Lat: {float(d[0]['lat']):.6f}, Lon: {float(d[0]['lon']):.6f}")
    except Exception as e:
        print(f"{q:35} -> Error: {e}")
