import json

def find_listings_arr(obj, depth=0):
    if depth > 15: return None
    if isinstance(obj, dict):
        if 'listings' in obj and isinstance(obj['listings'], list) and len(obj['listings']) > 3:
            return obj['listings']
        for v in obj.values():
            r = find_listings_arr(v, depth+1)
            if r: return r
    elif isinstance(obj, list):
        for i in obj:
            r = find_listings_arr(i, depth+1)
            if r: return r
    return None

data = json.load(open('datalake_poligono.json', encoding='utf-8'))

with open("ev_test.html", encoding="utf-8") as f:
    import bs4
    soup = bs4.BeautifulSoup(f.read(), "html.parser")
    nd = soup.find("script", id="__NEXT_DATA__")
    data_ev = json.loads(nd.get_text())

listings = find_listings_arr(data_ev)
print("Listing keys:", listings[0]["listing"].keys())
for k, v in listings[0]["listing"].items():
    if isinstance(v, dict):
        print(f"  {k} -> {v.keys()}")

# Look recursively for lat in listing
def find_lat(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ['lat', 'latitude', 'lng', 'longitude', 'location', 'coord', 'coordinates']:
                print(f"FOUND: {path}.{k} = {v}")
            find_lat(v, path + "." + k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_lat(item, path + f"[{i}]")

print("\nSearching for lat inside listing[0]...")
find_lat(listings[0]["listing"], "listing")
