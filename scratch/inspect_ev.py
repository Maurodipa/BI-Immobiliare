from bs4 import BeautifulSoup
import json, re

soup = BeautifulSoup(open('ev_debug.html', encoding='utf-8').read(), 'html.parser')
data = json.loads(soup.find('script', id='__NEXT_DATA__').get_text())

txt = json.dumps(data)
for field in ['totalCount', 'pageCount', 'totalPages', 'totalResults', 'numHits', 'pagination']:
    idx = txt.find(field)
    if idx >= 0:
        print(f'{field}: ...{txt[idx:idx+80]}...')

# Also show the URL pattern used for pagination
print()
# Find the displayId of all listings and build URL
def find_key(obj, key, depth=0):
    if depth > 15: return None
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], list) and len(obj[key]) > 10:
            return obj[key]
        for v in obj.values():
            result = find_key(v, key, depth+1)
            if result: return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_key(item, key, depth+1)
            if result: return result
    return None

listings = find_key(data, 'listings')
print(f'Listings on this page: {len(listings)}')
print()
# Sample: extract all useful fields from each listing
for item in listings[:3]:
    l = item['listing']
    display_id = l.get('displayId', 'N/A')
    title = (l.get('profile') or {}).get('title', 'N/A')
    price = (l.get('price') or {}).get('salesPrice', {}).get('min', 0)
    area = (l.get('area') or {}).get('totalSurface', {}).get('min', 0)
    rooms = (l.get('rooms') or {}).get('min', 0)
    neighborhood = next((c['text'] for c in l.get('addressComponents', []) if c['placeType'] == 'neighborhood'), 'N/A')
    city = next((c['text'] for c in l.get('addressComponents', []) if c['placeType'] == 'locality'), 'N/A')
    url = f"https://www.engelvoelkers.com/it/it/proprieta/{display_id.lower()}"
    print(f"ID: {display_id} | {title}")
    print(f"  Prezzo: {price} | Area: {area}mq | Stanze: {rooms}")
    print(f"  Zona: {neighborhood}, {city}")
    print(f"  URL: {url}")
    print()
