from seleniumbase import SB
import time, json
from bs4 import BeautifulSoup

# Proviamo il path dedicato /lazio/roma/ che abbiamo visto nel menu
urls_to_try = [
    "https://www.engelvoelkers.com/it/it/proprieta/res/vendita/immobili/lazio/roma?pageSize=18&facets=subTypology:apartment;&facets=priceMax:600000;",
    "https://www.engelvoelkers.com/it/it/proprieta/res/vendita/immobili/lazio/roma/?pageSize=18",
    "https://www.engelvoelkers.com/it/it/proprieta/res/vendita/immobili?businessArea=residential&facets=subTypology:apartment;&facets=commercializationType:buy;&facets=cityName:Roma;&facets=priceMax:600000;&pageSize=18",
]

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

with SB(uc=True, headless=False) as sb:
    for url in urls_to_try:
        print(f"\nTest: {url[:100]}")
        sb.uc_open_with_reconnect(url, 5)
        time.sleep(3)
        actual_url = sb.get_current_url()
        print(f"  -> Redirect: {actual_url[:120]}")
        src = sb.get_page_source()
        soup = BeautifulSoup(src, "html.parser")
        nd = soup.find("script", id="__NEXT_DATA__")
        if nd:
            data = json.loads(nd.get_text())
            listings = find_listings_arr(data)
            if listings:
                print(f"  Listings: {len(listings)}")
                cities = set()
                for item in listings:
                    l = item["listing"]
                    city = next((c["text"] for c in l.get("addressComponents", []) if c["placeType"] == "locality"), "N/A")
                    cities.add(city)
                print(f"  Città trovate: {cities}")
            else:
                print("  Nessun listing")
        else:
            print("  No NEXT_DATA (probabile captcha)")
