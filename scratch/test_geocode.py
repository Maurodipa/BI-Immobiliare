import requests
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

queries = [
    "Via Torbole, Roma",
    "Pantano Borghese, Roma",
    "Casetta Mattei, Roma"
]

headers = {'User-Agent': 'BI_Immobiliare_Agent/1.0'}

for q in queries:
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    r = requests.get(url, headers=headers, verify=False)
    data = r.json()
    if data:
        print(f"'{q}' -> {data[0]['lat']}, {data[0]['lon']}")
    else:
        print(f"'{q}' -> NOT FOUND")
    time.sleep(1.1)
