import json

with open('datalake_roma.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('| # | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Storico Prezzi (€) | Sup (mq) | Stanze | Piano | Stato | Date Ricerca |')
print('|---|---|---|---|---|---|---|---|---|---|---|')

for i, item in enumerate(data, 1):
    titolo_raw = (item.get('titolo') or 'Annuncio').replace('|', '-').strip()
    if len(titolo_raw) > 30:
        titolo = titolo_raw[:27] + '...'
    else:
        titolo = titolo_raw

    urls = item.get('url_sorgenti', [])
    if len(urls) == 1:
        links_str = f"[Link 1]({urls[0]})"
    elif len(urls) > 1:
        links_str = ", ".join([f"[Link {idx+1}]({u})" for idx, u in enumerate(urls)])
    else:
        links_str = "N/A"

    zona = (item.get('indirizzo_zona') or item.get('zona') or 'N/A')
    if len(zona) > 18:
        zona = zona[:15] + '...'

    prezzo_num = item.get('prezzo_attuale', 0)
    prezzo_attuale = f"€ {prezzo_num:,}".replace(',', '.') if prezzo_num > 0 else "N/A"

    # Storico prezzi
    storico = item.get('storico_prezzi', [])
    prezzi_list = [f"€ {p['prezzo']:,}".replace(',', '.') for p in storico if p.get('prezzo', 0) > 0]
    storico_str = " -> ".join(prezzi_list) if prezzi_list else "N/A"

    sup = item.get('superficie', 0)
    stanze = item.get('numero_stanze', 0)
    piano = item.get('piano', 'N/A')
    stato_raw = item.get('stato_annuncio', 'N/A')
    stato = "Attivo" if stato_raw == "Attivo" else "Non piu visibile"
    date_res = ', '.join(item.get('date_market_research', []))

    print(f'| {i} | {titolo} | {links_str} | {zona} | {prezzo_attuale} | {storico_str} | {sup} | {stanze} | {piano} | {stato} | {date_res} |')
