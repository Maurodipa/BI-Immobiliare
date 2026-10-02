import json

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Separiamo in Attivi e Non più visibili
attivi = [d for d in data if d.get('stato_annuncio') == 'Attivo']
non_visibili = [d for d in data if d.get('stato_annuncio') != 'Attivo']

# Ordiniamo ciascun gruppo per prezzo_attuale (crescente)
attivi.sort(key=lambda x: x.get('prezzo_attuale', 0))
non_visibili.sort(key=lambda x: x.get('prezzo_attuale', 0))

sorted_data = attivi + non_visibili

print('| # | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Prezzo (€/mq) | Storico / Variazioni Prezzi (€) | Sup (mq) | Stanze | Piano | Stato | Date Ricerca |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|')

for i, item in enumerate(sorted_data, 1):
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

    sup = item.get('superficie', 0)
    
    # Prezzo al mq
    if prezzo_num > 0 and sup > 0:
        prezzo_mq_num = round(prezzo_num / sup)
        prezzo_mq = f"€ {prezzo_mq_num:,}".replace(',', '.') + " /mq"
    else:
        prezzo_mq = "N/A"

    # Storico prezzi
    storico = item.get('storico_prezzi', [])
    prezzi_list = [f"€ {p['prezzo']:,}".replace(',', '.') for p in storico if p.get('prezzo', 0) > 0]
    # Rimuoviamo duplicati consecutivi per pulizia
    clean_history = []
    for p in prezzi_list:
        if not clean_history or clean_history[-1] != p:
            clean_history.append(p)
    storico_str = " -> ".join(clean_history) if clean_history else "N/A"

    stanze = item.get('numero_stanze', 0)
    piano = item.get('piano', 'N/A')
    stato_raw = item.get('stato_annuncio', 'N/A')
    stato = "Attivo" if stato_raw == "Attivo" else "Non piu visibile"
    date_res = ', '.join(item.get('date_market_research', []))

    print(f'| {i} | {titolo} | {links_str} | {zona} | {prezzo_attuale} | {prezzo_mq} | {storico_str} | {sup} | {stanze} | {piano} | {stato} | {date_res} |')
