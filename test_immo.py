from curl_cffi import requests
import time

url = "https://www.immobiliare.it/vendita-case/roma/centro/?criterio=rilevanza&prezzoMassimo=600000&localiMinimo=3&pianoMinimo=2&ascensore=1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}

response = requests.get(url, headers=headers, impersonate="chrome110")
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    with open("immo_test.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Saved to immo_test.html")
else:
    print(response.text[:500])
