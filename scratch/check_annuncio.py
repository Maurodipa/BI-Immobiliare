from seleniumbase import SB
from bs4 import BeautifulSoup
import json
import re

url = "https://www.immobiliare.it/annunci/129015830/"

with SB(uc=True, headless=True) as sb:
    sb.open(url)
    sb.sleep(4)
    html = sb.get_page_source()
    with open("scratch/annuncio_129015830.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Page length:", len(html))
    
    title = sb.get_title()
    print("Page title:", title)
