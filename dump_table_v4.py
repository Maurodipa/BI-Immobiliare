import json
import re

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Separiamo nelle categorie richieste
attivi = []
aste = []
c1_c2 = []
non_visibili = []

def is_c1_c2(titolo):
    t = titolo.upper()
    return any(x in t for x in ["C1", "C2", "C/1", "C/2", "NEGOZIO", "MAGAZZINO", "OPEN SPACE", "LOFT"])

def is_asta(titolo):
    return "ALL'ASTA" in titolo.upper() or "ASTA" in titolo.upper()

for d in data:
    if d.get('stato_annuncio') == 'Attivo':
        titolo = d.get('titolo', '')
        if is_c1_c2(titolo):
            c1_c2.append(d)
        elif is_asta(titolo):
            aste.append(d)
        else:
            attivi.append(d)
    else:
        non_visibili.append(d)

def get_sort_key(x):
    dates = x.get('date_market_research', [])
    data_scoperta = dates[0] if dates else '9999-99-99'
    return (data_scoperta, x.get('prezzo_attuale', 0))

attivi.sort(key=get_sort_key)
aste.sort(key=get_sort_key)
c1_c2.sort(key=get_sort_key)
non_visibili.sort(key=get_sort_key)

def print_table(group, title, is_history=False):
    if not group:
        return ""
    
    out = f"### {title}\n\n"
    if is_history:
        out += "| # | Portale | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Prezzo (€/mq) | Sup (mq) | Stanze | Piano | Data Scoperta | Data Rimozione |\n"
        out += "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    else:
        out += "| # | Portale | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Prezzo (€/mq) | Sup (mq) | Stanze | Piano | Data Scoperta |\n"
        out += "|---|---|---|---|---|---|---|---|---|---|---|\n"
    
    for i, item in enumerate(group, 1):
        titolo_raw = (item.get('titolo') or 'Annuncio').replace('|', '-').strip()
        portale_raw = item.get('nome_portale', '')
        portale = "E&V" if "engel" in portale_raw.lower() else "🏠"
        
        links = []
        for idx, link in enumerate(item.get('url_sorgenti', [])):
            links.append(f"[Link {idx+1}]({link})")
        link_str = ", ".join(links)
        
        zona = (item.get('indirizzo_zona') or 'N/A').replace('|', '-').strip()
        prezzo = item.get('prezzo_attuale', 0)
        sup = item.get('superficie')
        sup = int(sup) if sup else 0
        mq_price = int(prezzo/sup) if sup > 0 else 0
        stanze = item.get('numero_stanze', 'N/A')
        piano = item.get('piano', 'N/A')
        
        prezzo_fmt = f"€ {prezzo:,}".replace(',', '.')
        mq_fmt = f"€ {mq_price:,}".replace(',', '.') + " /mq"
        
        # Data Scoperta = the first date in date_market_research
        dates = item.get('date_market_research', [])
        data_scoperta = dates[0] if dates else "N/A"
        
        if is_history:
            rimozione = item.get('data_rimozione', 'N/A')
            out += f"| {i} | {portale} | {titolo_raw} | {link_str} | {zona} | {prezzo_fmt} | {mq_fmt} | {sup} | {stanze} | {piano} | {data_scoperta} | {rimozione} |\n"
        else:
            out += f"| {i} | {portale} | {titolo_raw} | {link_str} | {zona} | {prezzo_fmt} | {mq_fmt} | {sup} | {stanze} | {piano} | {data_scoperta} |\n"
            
    return out + "\n"

full_out = "# Datalake - Poligono Personalizzato (Suddiviso per Categorie)\n\n"
full_out += print_table(attivi, "🟢 Appartamenti Standard Attivi")
full_out += print_table(c1_c2, "🟣 Locali C1, C2, Open Space e Loft")
full_out += print_table(aste, "🔨 Aste Immobiliari")
full_out += print_table(non_visibili, "🔴 Storico Annunci Non Più Visibili", is_history=True)

with open('tabella_poligono_categorizzata.md', 'w', encoding='utf-8') as f:
    f.write(full_out)

print("Generazione completata in tabella_poligono_categorizzata.md")
