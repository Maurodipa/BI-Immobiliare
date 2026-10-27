import requests, urllib3
urllib3.disable_warnings()
headers = {'User-Agent': 'BI_Immobiliare_Agent/1.0'}
for q in ['via Del Gesù, 00186 Roma', "via Sant'ambrogio, 00186 Roma", 'via Beato Angelico, 00186 Roma']:
    r = requests.get(f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1', headers=headers, verify=False)
    data = r.json()
    if data:
        print(f"{q} -> {data[0]['lat']}, {data[0]['lon']}")
    else:
        print(f"{q} -> NOT FOUND")
