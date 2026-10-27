import requests, json, urllib3
urllib3.disable_warnings()

url = 'https://nominatim.openstreetmap.org/search?q=Trastevere,+Roma&format=json&polygon_geojson=1&limit=1'
r = requests.get(url, headers={'User-Agent': 'test'}, timeout=5, verify=False)
res = r.json()
if res:
    print("Bounding box:", res[0].get("boundingbox"))
    if "geojson" in res[0]:
        print("GeoJSON type:", res[0]["geojson"]["type"])
        coords = res[0]["geojson"]["coordinates"]
        with open("scratch/trastevere_boundary.json", "w", encoding="utf-8") as f:
            json.dump(res[0]["geojson"], f, indent=2)
        print("Saved to scratch/trastevere_boundary.json")
