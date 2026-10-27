import json
import re
import datetime

TODAY = datetime.date.today()

def format_date_with_age(date_str):
    if not date_str or date_str == "N/A":
        return "N/A"
    try:
        d = datetime.date.fromisoformat(str(date_str).strip()[:10])
        delta = (TODAY - d).days
        if delta == 0:
            return f"{d.isoformat()} (Oggi)"
        elif delta == 1:
            return f"{d.isoformat()} (1 g fa)"
        else:
            return f"{d.isoformat()} ({delta} gg fa)"
    except Exception:
        return str(date_str)

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Separiamo nelle categorie richieste
attivi = []
aste = []
c1_c2 = []
non_visibili = []
scartati = []

def is_c1_c2(titolo):
    t = titolo.upper()
    return any(x in t for x in ["C1", "C2", "C/1", "C/2", "NEGOZIO", "MAGAZZINO", "OPEN SPACE", "LOFT", "UFFICIO", "STUDIO"])

def is_asta(d):
    t = d.get('titolo', '').upper()
    urls = [u.upper() for u in d.get('url_sorgenti', [])]
    return "ASTA" in t or "NUDA PROPRIET" in t or any("ASTA" in u for u in urls)

for d in data:
    if d.get('stato_annuncio') == 'Scartato':
        scartati.append(d)
    elif d.get('stato_annuncio') == 'Attivo':
        titolo = d.get('titolo', '')
        if is_c1_c2(titolo):
            c1_c2.append(d)
        elif is_asta(d):
            aste.append(d)
        else:
            attivi.append(d)
    else:
        non_visibili.append(d)

def extract_street(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico|arco|salita|rampa)\s+([^,]+)', title, re.IGNORECASE)
    if match:
        street = match.group(0).strip().lower()
        # Strip s.n.c, house numbers and trailing punctuation so 'Via della Reginella 6' matches 'Via della Reginella, 6'
        street = re.sub(r'\s+s\.n\.c|\s+\d+.*$', '', street, flags=re.IGNORECASE).strip()
        return street
    # Pattern Idealista: "Trilocale in Catania, 69, Trevi, Roma"
    m_in = re.search(r'in\s+([A-Za-zÀ-ÿ\s\'-]+?)(?:,\s*\d+)?,\s*[^,]+,\s*Roma', title, re.IGNORECASE)
    if m_in:
        candidate = m_in.group(1).strip().lower()
        if candidate not in ["vendita", "affitto", "asta"]:
            return candidate
    return ""

def deduplicate_group(group):
    merged = []
    generic_zones = {"", "n/a", "roma", "centro", "centro storico", "2 locali", "3 locali", "4 locali", "5 locali", "tridente"}
    for apt in group:
        found = False
        for m in merged:
            via_apt = extract_street(apt.get('titolo', ''))
            via_m = extract_street(m.get('titolo', ''))
            
            stessa_via = False
            if via_apt and via_m:
                stessa_via = (via_apt == via_m)
            elif not via_apt and not via_m:
                z_m = m.get('indirizzo_zona', '').strip().lower()
                z_apt = apt.get('indirizzo_zona', '').strip().lower()
                if z_m not in generic_zones and z_apt not in generic_zones:
                    stessa_via = (z_m == z_apt)
                
            # If same street, same rooms, and similar size (±5mq), we consider it the same apartment
            if (stessa_via and 
                str(m.get('numero_stanze')) == str(apt.get('numero_stanze')) and 
                abs(int(m.get('superficie') or 0) - int(apt.get('superficie') or 0)) <= 5):
                
                found = True
                
                # Merge URLs
                urls_m = set(m.get('url_sorgenti', []))
                for url in apt.get('url_sorgenti', []):
                    urls_m.add(url)
                m['url_sorgenti'] = list(urls_m)
                
                # Merge portale labels
                m['portali_set'].add(apt.get('nome_portale', ''))
                
                # Merge prices
                if apt.get('prezzo_attuale'):
                    m['prezzi_multipli'].add(apt.get('prezzo_attuale'))
                    
                # Merge storico_prezzi
                if 'storico_prezzi' not in m:
                    m['storico_prezzi'] = []
                for sp in apt.get('storico_prezzi', []):
                    if sp not in m['storico_prezzi']:
                        m['storico_prezzi'].append(sp)
                break
                
        if not found:
            apt_copy = apt.copy()
            apt_copy['prezzi_multipli'] = {apt_copy.get('prezzo_attuale', 0)}
            apt_copy['portali_set'] = {apt_copy.get('nome_portale', '')}
            apt_copy['storico_prezzi'] = list(apt_copy.get('storico_prezzi', []))
            merged.append(apt_copy)
            
    return merged

def get_price_variation(item):
    storico = item.get('storico_prezzi', [])
    prezzi_multipli = sorted([p for p in item.get('prezzi_multipli', {item.get('prezzo_attuale', 0)}) if p > 0])
    
    # 1. Variazione storica nel tempo (ribassi o aumenti registrati)
    if storico and len(storico) >= 2:
        by_date = {}
        for s in storico:
            dt = s.get('data_rilevazione', '')
            p = s.get('prezzo', 0)
            if dt and p > 0:
                by_date.setdefault(dt, []).append(p)
                
        dates = sorted(by_date.keys())
        if len(dates) >= 2:
            first_date = dates[0]
            last_date = dates[-1]
            
            # Se i prezzi sono cambiati tra prima e ultima data
            if set(by_date[first_date]) != set(by_date[last_date]):
                p_initial = by_date[first_date][0]
                p_current = by_date[last_date][-1]
                diff = p_current - p_initial
                if diff != 0:
                    pct = (diff / p_initial) * 100
                    diff_abs = f"{abs(diff):,}".replace(',', '.')
                    p_init_fmt = f"{p_initial:,}".replace(',', '.')
                    if diff < 0:
                        return f"📉 -€ {diff_abs} (-{abs(pct):.1f}%) [da € {p_init_fmt}]"
                    else:
                        return f"📈 +€ {diff_abs} (+{pct:.1f}%) [da € {p_init_fmt}]"
                        
    # 2. Differenza tra portali diversi per lo stesso immobile
    if len(prezzi_multipli) > 1:
        delta = max(prezzi_multipli) - min(prezzi_multipli)
        if delta > 0:
            delta_fmt = f"{delta:,}".replace(',', '.')
            return f"⚖️ Δ € {delta_fmt} tra portali"
            
    return "-"

def get_sort_key(x):
    # Sort by the lowest price found
    prezzi = x.get('prezzi_multipli', {x.get('prezzo_attuale', 0)})
    return min(prezzi) if prezzi else 0

attivi = deduplicate_group(attivi)
aste = deduplicate_group(aste)
c1_c2 = deduplicate_group(c1_c2)
non_visibili = deduplicate_group(non_visibili)
scartati = deduplicate_group(scartati)

attivi.sort(key=get_sort_key)
aste.sort(key=get_sort_key)
c1_c2.sort(key=get_sort_key)
non_visibili.sort(key=get_sort_key)
scartati.sort(key=get_sort_key)

def print_table(group, title, is_history=False):
    if not group:
        return ""
    
    out = f"### {title} ({len(group)})\n\n"
    if is_history:
        out += "| # | Valutazione | Portale | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Variazione Prezzo | Prezzo (€/mq) | Sup (mq) | Stanze | Piano | Data Aggiunta | Data Rimozione | Data Pubblicazione |\n"
        out += "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    else:
        out += "| # | Valutazione | Portale | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Variazione Prezzo | Prezzo (€/mq) | Sup (mq) | Stanze | Piano | Data Aggiunta | Data Pubblicazione |\n"
        out += "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    
    for i, item in enumerate(group, 1):
        titolo_raw = (item.get('titolo') or 'Annuncio').replace('|', '-').strip()
        
        # Format portals based on all source URLs
        portali_icone = []
        for url in item.get('url_sorgenti', []):
            url_lower = url.lower()
            if "engel" in url_lower and "E&V" not in portali_icone:
                portali_icone.append("E&V")
            elif "idealista" in url_lower and "🔵" not in portali_icone:
                portali_icone.append("🔵")
            elif "immobiliare" in url_lower and "🏠" not in portali_icone:
                portali_icone.append("🏠")
                
        # Fallback if no URLs match known patterns
        if not portali_icone:
            p_lower = item.get('nome_portale', '').lower()
            if "engel" in p_lower: portali_icone.append("E&V")
            elif "idealista" in p_lower: portali_icone.append("🔵")
            else: portali_icone.append("🏠")
            
        portale = " + ".join(portali_icone)
        
        links = []
        for idx, link in enumerate(item.get('url_sorgenti', [])):
            links.append(f"[Link {idx+1}]({link})")
        link_str = ", ".join(links)
        
        zona = (item.get('indirizzo_zona') or 'N/A').replace('|', '-').strip()
        
        # Format prices
        prezzi = sorted(list(item.get('prezzi_multipli', {item.get('prezzo_attuale', 0)})))
        if not prezzi or prezzi == [0]:
            prezzo_fmt = "N/A"
            mq_fmt = "N/A"
        else:
            prezzi_str = []
            for p in prezzi:
                if p > 0:
                    prezzi_str.append(f"€ {p:,}".replace(',', '.'))
            prezzo_fmt = " / ".join(prezzi_str)
            
            sup = item.get('superficie')
            sup = int(sup) if sup else 0
            
            mq_str = []
            for p in prezzi:
                if p > 0 and sup > 0:
                    mq_str.append(f"€ {int(p/sup):,}".replace(',', '.'))
            mq_fmt = " / ".join(mq_str) + " /mq" if mq_str else "N/A"
        
        sup = item.get('superficie')
        sup = int(sup) if sup else 0
        stanze = item.get('numero_stanze', 'N/A')
        piano = item.get('piano', 'N/A')
        
        # Data Aggiunta = first date in date_market_research
        dates = item.get('date_market_research', [])
        raw_data_agg = dates[0] if dates else "N/A"
        data_aggiunta = format_date_with_age(raw_data_agg)
        data_pub = item.get('data_pubblicazione') or "N/A"
        
        valutazione = item.get('valutazione', '⏳ Da valutare')
        var_prezzo = get_price_variation(item)
        
        if is_history:
            rimozione = item.get('data_rimozione', 'N/A')
            out += f"| {i} | {valutazione} | {portale} | {titolo_raw} | {link_str} | {zona} | {prezzo_fmt} | {var_prezzo} | {mq_fmt} | {sup} | {stanze} | {piano} | {data_aggiunta} | {rimozione} | {data_pub} |\n"
        else:
            out += f"| {i} | {valutazione} | {portale} | {titolo_raw} | {link_str} | {zona} | {prezzo_fmt} | {var_prezzo} | {mq_fmt} | {sup} | {stanze} | {piano} | {data_aggiunta} | {data_pub} |\n"
            
    return out + "\n"

# --- Trova gli annunci nuovi (dalla scansione più recente) ---
# Per ciascun annuncio deduplicated, la "data_scoperta" è il primo elemento di date_market_research
# La scansione più recente è la data più alta trovata tra tutti gli attivi.
all_active_groups = attivi + aste + c1_c2
latest_scan_date = max(
    (item.get('date_market_research', ['1970-01-01'])[0] for item in all_active_groups),
    default='1970-01-01'
)
# Solo gli appartamenti standard vanno nei "Nuovi" (escludiamo Aste e C1/C2 dalla vetrina principale)
nuovi = [item for item in attivi if item.get('date_market_research', [''])[0] == latest_scan_date]
nuovi.sort(key=get_sort_key)

full_out = (
    "# Datalake Multi-Portale — Poligono Personalizzato Roma\n"
    "**Fonti:** immobiliare.it + Engel & Völkers + Idealista | **Filtri:** Min. 2 locali · Max € 700.000 · Roma centro\n\n"
    "> [!NOTE] I link puntano direttamente all'annuncio sul rispettivo portale.\n\n---\n\n"
)

# Sezione annunci nuovi in cima
if nuovi:
    full_out += f"### 🆕 Annunci Nuovi — Ultima Rilevazione del {latest_scan_date} ({len(nuovi)})\n\n"
    full_out += f"> [!IMPORTANT] Questi annunci sono stati rilevati per la prima volta nella scansione del {latest_scan_date}. Nelle scansioni successive più recenti (fino a oggi) non sono comparsi ulteriori nuovi immobili nel poligono. Rimangono qui come ultimi annunci nuovi finché non ne arrivano di più recenti.\n\n"
    full_out += "| # | Valutazione | Portale | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Variazione Prezzo | Prezzo (€/mq) | Sup (mq) | Stanze | Piano | Data Aggiunta | Data Pubblicazione |\n"
    full_out += "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"

    for i, item in enumerate(nuovi, 1):
        titolo_raw = (item.get('titolo') or 'Annuncio').replace('|', '-').strip()
        portali_icone = []
        for url in item.get('url_sorgenti', []):
            u = url.lower()
            if "engel" in u and "E&V" not in portali_icone: portali_icone.append("E&V")
            elif "idealista" in u and "🔵" not in portali_icone: portali_icone.append("🔵")
            elif "immobiliare" in u and "🏠" not in portali_icone: portali_icone.append("🏠")
        if not portali_icone:
            p = item.get('nome_portale', '').lower()
            portali_icone.append("E&V" if "engel" in p else "🔵" if "idealista" in p else "🏠")
        portale = " + ".join(portali_icone)

        links = [f"[Link {idx+1}]({lnk})" for idx, lnk in enumerate(item.get('url_sorgenti', []))]
        link_str = ", ".join(links)
        zona = (item.get('indirizzo_zona') or 'N/A').replace('|', '-').strip()
        prezzi = sorted(list(item.get('prezzi_multipli', {item.get('prezzo_attuale', 0)})))
        prezzi_str = [f"€ {p:,}".replace(',', '.') for p in prezzi if p > 0]
        prezzo_fmt = " / ".join(prezzi_str) if prezzi_str else "N/A"
        sup = int(item.get('superficie') or 0)
        mq_str = [f"€ {int(p/sup):,}".replace(',', '.') for p in prezzi if p > 0 and sup > 0]
        mq_fmt = " / ".join(mq_str) + " /mq" if mq_str else "N/A"
        stanze = item.get('numero_stanze', 'N/A')
        piano = item.get('piano', 'N/A')
        valutazione = item.get('valutazione', '⏳ Da valutare')

        dates = item.get('date_market_research', [])
        raw_data_agg = dates[0] if dates else "N/A"
        data_aggiunta = format_date_with_age(raw_data_agg)
        data_pub = item.get('data_pubblicazione') or "N/A"
        var_prezzo = get_price_variation(item)

        full_out += f"| {i} | {valutazione} | {portale} | {titolo_raw} | {link_str} | {zona} | {prezzo_fmt} | {var_prezzo} | {mq_fmt} | {sup} | {stanze} | {piano} | {data_aggiunta} | {data_pub} |\n"

    full_out += "\n---\n\n"

# Sezione variazioni di prezzo in evidenza
con_variazioni = [item for item in attivi if get_price_variation(item) != "-"]
if con_variazioni:
    con_variazioni.sort(key=get_sort_key)
    full_out += f"### 📉 Variazioni di Prezzo Rilevate ({len(con_variazioni)})\n\n"
    full_out += "> [!TIP] Questa sezione evidenzia tutti gli immobili attivi che hanno registrato un ribasso di prezzo nel tempo (📉) o che presentano discrepanze di prezzo tra diversi portali/annunci per la stessa proprietà (⚖️).\n\n"
    full_out += "| # | Valutazione | Portale | Titolo Annuncio | Link Sorgenti | Zona / Indirizzo | Prezzo Attuale (€) | Variazione Prezzo | Prezzo (€/mq) | Sup (mq) | Stanze | Piano | Data Aggiunta |\n"
    full_out += "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"

    for i, item in enumerate(con_variazioni, 1):
        titolo_raw = (item.get('titolo') or 'Annuncio').replace('|', '-').strip()
        portali_icone = []
        for url in item.get('url_sorgenti', []):
            u = url.lower()
            if "engel" in u and "E&V" not in portali_icone: portali_icone.append("E&V")
            elif "idealista" in u and "🔵" not in portali_icone: portali_icone.append("🔵")
            elif "immobiliare" in u and "🏠" not in portali_icone: portali_icone.append("🏠")
        if not portali_icone:
            p = item.get('nome_portale', '').lower()
            portali_icone.append("E&V" if "engel" in p else "🔵" if "idealista" in p else "🏠")
        portale = " + ".join(portali_icone)

        links = [f"[Link {idx+1}]({lnk})" for idx, lnk in enumerate(item.get('url_sorgenti', []))]
        link_str = ", ".join(links)
        zona = (item.get('indirizzo_zona') or 'N/A').replace('|', '-').strip()
        prezzi = sorted(list(item.get('prezzi_multipli', {item.get('prezzo_attuale', 0)})))
        prezzi_str = [f"€ {p:,}".replace(',', '.') for p in prezzi if p > 0]
        prezzo_fmt = " / ".join(prezzi_str) if prezzi_str else "N/A"
        sup = int(item.get('superficie') or 0)
        mq_str = [f"€ {int(p/sup):,}".replace(',', '.') for p in prezzi if p > 0 and sup > 0]
        mq_fmt = " / ".join(mq_str) + " /mq" if mq_str else "N/A"
        stanze = item.get('numero_stanze', 'N/A')
        piano = item.get('piano', 'N/A')
        valutazione = item.get('valutazione', '⏳ Da valutare')

        dates = item.get('date_market_research', [])
        raw_data_agg = dates[0] if dates else "N/A"
        data_aggiunta = format_date_with_age(raw_data_agg)
        var_prezzo = get_price_variation(item)

        full_out += f"| {i} | {valutazione} | {portale} | {titolo_raw} | {link_str} | {zona} | {prezzo_fmt} | {var_prezzo} | {mq_fmt} | {sup} | {stanze} | {piano} | {data_aggiunta} |\n"

    full_out += "\n---\n\n"

full_out += print_table(attivi, "🟢 Appartamenti Standard Attivi")
full_out += "---\n\n" + print_table(c1_c2, "🟣 Locali C1, C2, Open Space e Loft")
full_out += "---\n\n" + print_table(aste, "🔨 Aste Immobiliari")
full_out += "---\n\n" + print_table(scartati, "🗑️ Annunci Scartati")
full_out += "---\n\n" + print_table(non_visibili, "🔴 Storico Annunci Non Più Visibili", is_history=True)

with open('tabella_poligono_categorizzata.md', 'w', encoding='utf-8') as f:
    f.write(full_out)

print("Generazione completata in tabella_poligono_categorizzata.md")
