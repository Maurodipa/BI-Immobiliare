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

with SB(uc=True, headless=True) as sb:
    url = "https://www.engelvoelkers.com/it/it/ricerca?placeId=ChIJu46S-ZZhLxMROG5lkwZ3uvM&businessArea=residential&transactionType=buy&price=%3A600000&rooms=2%3A&page=1"
    sb.uc_open_with_reconnect(url, 6)
    src = sb.get_page_source()
    soup = BeautifulSoup(src, "html.parser")
    nd = soup.find("script", id="__NEXT_DATA__")
    if nd:
        data = json.loads(nd.get_text())
        listings = find_listings_arr(data)
        if listings:
            for item in listings[:5]:
                l = item.get("listing", {})
                print("Display ID:", l.get("displayId"))
                print("Keys:", list(l.keys()))
                if "url" in l: print("url:", l.get("url"))
                if "link" in l: print("link:", l.get("link"))
                if "slug" in l: print("slug:", l.get("slug"))
                if "uri" in l: print("uri:", l.get("uri"))
                # Also check profile or other nested dicts
                for k, v in l.items():
                    if isinstance(v, dict):
                        for sub_k in v.keys():
                            if 'url' in sub_k.lower() or 'link' in sub_k.lower() or 'href' in sub_k.lower():
                                print(f"Nested {k}.{sub_k}:", v[sub_k])
                    elif isinstance(v, str) and ('/' in v or 'http' in v):
                        print(f"Str field {k}:", v)
