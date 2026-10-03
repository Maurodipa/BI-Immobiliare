import json, re
from bs4 import BeautifulSoup
soup = BeautifulSoup(open("ev_test.html", encoding="utf-8").read(), "html.parser")
nd = soup.find("script", id="__NEXT_DATA__")
text = nd.get_text()
for m in re.finditer(r".{0,40}\"lat\".{0,40}", text):
    print(m.group(0))
