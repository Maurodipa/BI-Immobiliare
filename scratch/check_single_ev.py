import requests
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
url = "https://www.engelvoelkers.com/it/it/proprieta/w-04bjqr"
r = requests.get(url, verify=False)
text = r.text
print("Coordinates found:")
for m in re.finditer(r".{0,40}\"lat\":.{0,40}", text):
    print(m.group(0))
