import json
from seleniumbase import SB
from bs4 import BeautifulSoup

def find_listings_arr(obj, depth=0):
    if depth > 15:
        return None
    if isinstance(obj, dict):
        if 'listings' in obj and isinstance(obj['listings'], list) and len(obj['listings']) > 3:
            return obj['listings']
        for v in obj.values():
            r = find_listings_arr(v, depth + 1)
            if r:
                return r
    elif isinstance(obj, list):
        for i in obj:
            r = find_listings_arr(i, depth + 1)
            if r:
                return r
    return None

with SB(uc=True, headless=False) as sb:
    url = "https://www.engelvoelkers.com/it/it/ricerca?placeId=ChIJu46S-ZZhLxMROG5lkwZ3uvM&businessArea=residential&transactionType=buy&price=%3A600000&rooms=2%3A&page=1"
    sb.uc_open_with_reconnect(url, 6)
    src = sb.get_page_source()
    soup = BeautifulSoup(src, "html.parser")
    nd = soup.find("script", id="__NEXT_DATA__")
    if nd:
        data = json.loads(nd.get_text())
        listings = find_listings_arr(data)
        if listings:
            l = listings[0].get("listing", {})
            with open("scratch/sample_ev_listing.json", "w", encoding="utf-8") as f:
                json.dump(l, f, indent=2, ensure_ascii=False)
            print("Successfully dumped sample_ev_listing.json")
