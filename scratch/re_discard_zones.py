import json

ZONE_ROSSE = [
    "parioli", "flaminio", "prati", "delle vittorie", "borgo", "aurelio", 
    "trionfale", "testaccio", "aventino", "san saba", "esquilino", 
    "celio", "macao", "castro pretorio", "ludovisi", "sallustiano",
    "termini", "turati"
]

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for d in data:
    t = d.get('titolo', '').lower()
    z = d.get('indirizzo_zona', '').lower()
    # Scarta se in zone rosse
    if any(zr in t or zr in z for zr in ZONE_ROSSE):
        if d.get('stato_annuncio') != 'Scartato':
            d['stato_annuncio'] = 'Scartato'
            count += 1
            print(f"Re-scartato zona rossa: {d.get('titolo')}")
            
    # Scarta se Icilio o Gemelli
    if 'icilio' in t or 'gemelli' in t:
        if d.get('stato_annuncio') != 'Scartato':
            d['stato_annuncio'] = 'Scartato'
            count += 1
            print(f"Re-scartato Icilio/Gemelli: {d.get('titolo')}")

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale ri-scartati: {count}")
