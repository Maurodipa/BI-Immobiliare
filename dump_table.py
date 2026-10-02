import json

with open('datalake_roma.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('| # | Titolo Annuncio (Cliccabile) | Zona / Indirizzo | Prezzo (€) | Sup (mq) | Stanze | Piano | Stato | Date Ricerca |')
print('|---|---|---|---|---|---|---|---|---|')
for i, item in enumerate(data, 1):
    titolo_raw = (item.get('titolo') or 'Annuncio').replace('|', '-').strip()
    urls = item.get('url_sorgenti', [])
    url = urls[0] if urls else '#'
    
    if len(titolo_raw) > 35:
        titolo_text = titolo_raw[:32] + '...'
    else:
        titolo_text = titolo_raw
        
    titolo_md = f"[{titolo_text}]({url})"
    
    zona = (item.get('indirizzo_zona') or item.get('zona') or 'N/A')
    if len(zona) > 20:
        zona = zona[:17] + '...'
        
    prezzo_num = item.get('prezzo_attuale', 0)
    prezzo = f"€ {prezzo_num:,}".replace(',', '.') if prezzo_num > 0 else "N/A"
    
    sup = item.get('superficie', 0)
    stanze = item.get('numero_stanze', 0)
    piano = item.get('piano', 'N/A')
    stato_raw = item.get('stato_annuncio', 'N/A')
    stato = "Attivo" if stato_raw == "Attivo" else "Non piu visibile"
    date_res = ', '.join(item.get('date_market_research', []))
    
    print(f'| {i} | {titolo_md} | {zona} | {prezzo} | {sup} | {stanze} | {piano} | {stato} | {date_res} |')
