import json

urls_to_discard = [
    'https://www.immobiliare.it/annunci/131338830/',
    'https://www.immobiliare.it/annunci/124762811/',
    'https://www.immobiliare.it/annunci/130243626/',
    'https://www.immobiliare.it/annunci/130614394/',
    'https://www.immobiliare.it/annunci/114263601/',
    'https://www.idealista.it/immobile/36695872/',
    'https://www.idealista.it/immobile/35854570/',
    'https://www.idealista.it/immobile/34821519/',
    'https://www.idealista.it/immobile/30907780/',
    'https://www.immobiliare.it/annunci/124657859/',
    'https://www.idealista.it/immobile/34149735/',
    'https://www.idealista.it/immobile/36814943/',
    'https://www.idealista.it/immobile/32803453/',
    'https://www.idealista.it/immobile/35805958/',
    'https://www.idealista.it/immobile/35854570/',
    'https://www.immobiliare.it/annunci/132501986/',
    'https://www.idealista.it/immobile/11876600/',
    'https://www.idealista.it/immobile/31325965/',
    'https://www.idealista.it/immobile/35614310/',
    'https://www.idealista.it/immobile/33798813/',
    'https://www.immobiliare.it/annunci/133241538/',
    'https://www.idealista.it/immobile/36041974/',
    'https://www.engelvoelkers.com/it/it/proprieta/w-04buwa',
    'https://www.idealista.it/immobile/36672902/',
    'https://www.idealista.it/immobile/35907573/',
    'https://www.idealista.it/immobile/35405090',
    'https://www.idealista.it/immobile/29016911/',
    'https://www.idealista.it/immobile/36665036/',
    'https://www.idealista.it/immobile/34969851/',
    'https://www.idealista.it/immobile/36041974/',
    'https://www.idealista.it/immobile/34385063/',
    'https://www.idealista.it/immobile/34755432/'
]

# Extract base IDs to make matching robust
ids_to_discard = []
for url in urls_to_discard:
    if 'immobiliare.it/annunci/' in url:
        ids_to_discard.append(url.split('annunci/')[1].split('/')[0].split('#')[0])
    elif 'idealista.it/immobile/' in url:
        ids_to_discard.append(url.split('immobile/')[1].split('/')[0].split('#')[0])
    elif 'engelvoelkers.com' in url:
        ids_to_discard.append('w-04buwa')

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for d in data:
    for url in d.get('url_sorgenti', []):
        if any(discard_id in url for discard_id in ids_to_discard):
            if d.get('stato_annuncio') != 'Scartato':
                d['stato_annuncio'] = 'Scartato'
                count += 1
                print(f"Scartato URL richiesto: {d.get('titolo')}")
            break

with open('datalake_poligono.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Totale scartati da URL: {count}")

# Now let's check what 'aste' are currently Active but not caught by our filter
aste_missed = 0
for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        title = d.get('titolo', '').lower()
        url_sorgenti = [u.lower() for u in d.get('url_sorgenti', [])]
        # Check if it's an auction
        is_asta = 'asta' in title or any('asta' in u for u in url_sorgenti) or d.get('prezzo_attuale', 0) % 10 != 0 # often auctions have weird prices
        if is_asta:
            print(f"Possibile asta non filtrata: {d.get('titolo')} - {d.get('prezzo_attuale')} - {d.get('url_sorgenti')}")
            aste_missed += 1

print(f"Totale possibili aste perse: {aste_missed}")
