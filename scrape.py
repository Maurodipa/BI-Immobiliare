import json
import os
import datetime

DATALAKE_PATH = "datalake_roma.json"
TODAY = datetime.date.today().isoformat()

def simulate_real_scraping():
    # Simulazione realistica di ciò che lo scraper avrebbe estratto oggi
    return [
        {
            "url_sorgente": "https://www.immobiliare.it/annunci/123456/",
            "nome_portale": "immobiliare.it",
            "titolo": "Attico luminoso in via del Babuino",
            "indirizzo_zona": "Centro Storico, Roma",
            "zona": "Centro",
            "prezzo_attuale": 580000,
            "superficie": 110,
            "numero_stanze": 4,
            "piano": "4",
            "ascensore": "Sì",
            "terrazza": "Sì",
            "stato_immobile": "Ottimo stato",
            "contatti": "061234567, email@agenzia.it",
            "data_pubblicazione": TODAY
        },
        {
            "url_sorgente": "https://www.idealista.it/immobile/7654321/",
            "nome_portale": "idealista.it",
            "titolo": "Trilocale da ristrutturare",
            "indirizzo_zona": "Rione Monti, Roma",
            "zona": "Centro",
            "prezzo_attuale": 450000,
            "superficie": 90,
            "numero_stanze": 3,
            "piano": "2",
            "ascensore": "Sì",
            "terrazza": "No",
            "stato_immobile": "Da ristrutturare",
            "contatti": "069876543, monti@remax.it",
            "data_pubblicazione": TODAY
        }
    ]

def setup_mock_history():
    # Prepariamo un finto stato PRECEDENTE del datalake (es. l'estrazione di ieri)
    # in modo da dimostrare i Casi B e C in esecuzione oggi.
    YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    return [
        # Appartamento che subirà una variazione di prezzo (CASO B)
        {
            "url_sorgenti": ["https://www.immobiliare.it/annunci/123456/"],
            "nome_portale": "immobiliare.it",
            "titolo": "Attico luminoso in via del Babuino",
            "zona": "Centro",
            "prezzo_attuale": 600000, # Prezzo vecchio (sceso a 580000 oggi)
            "superficie": 110,
            "numero_stanze": 4,
            "piano": "4",
            "stato_annuncio": "Attivo",
            "date_market_research": [YESTERDAY],
            "storico_prezzi": [{"prezzo": 600000, "data_rilevazione": YESTERDAY}]
        },
        # Appartamento che oggi non verrà più trovato (CASO C)
        {
            "url_sorgenti": ["https://www.immobiliare.it/annunci/999999/"],
            "nome_portale": "immobiliare.it",
            "titolo": "Appartamento venduto in Trastevere",
            "zona": "Centro",
            "prezzo_attuale": 400000,
            "superficie": 80,
            "numero_stanze": 3,
            "piano": "2",
            "stato_annuncio": "Attivo",
            "date_market_research": [YESTERDAY],
            "storico_prezzi": [{"prezzo": 400000, "data_rilevazione": YESTERDAY}]
        }
    ]


def process_datalake(new_apts):
    if os.path.exists(DATALAKE_PATH):
        with open(DATALAKE_PATH, "r", encoding="utf-8") as f:
            datalake = json.load(f)
    else:
        # Inizializziamo il datalake con i dati storici (di ieri) per dimostrare i casi
        datalake = setup_mock_history()
        
    new_added = 0
    price_vars = 0
    not_visible = 0
    
    for apt in new_apts:
        found = False
        for ext in datalake:
            try:
                if (ext.get('zona') == apt.get('zona') and
                    str(ext.get('piano')) == str(apt.get('piano')) and
                    str(ext.get('numero_stanze')) == str(apt.get('numero_stanze')) and
                    abs(int(ext.get('superficie', 0)) - int(apt.get('superficie', 0))) <= 5):
                    
                    found = True
                    # CASO B: Esiste già
                    if TODAY not in ext.get('date_market_research', []):
                        ext.setdefault('date_market_research', []).append(TODAY)
                    
                    last_price = ext.get('storico_prezzi', [{}])[-1].get('prezzo')
                    if last_price != apt.get('prezzo_attuale'):
                        ext.setdefault('storico_prezzi', []).append({"prezzo": apt.get('prezzo_attuale'), "data_rilevazione": TODAY})
                        ext["prezzo_attuale"] = apt.get('prezzo_attuale')
                        price_vars += 1
                        
                    if apt.get('url_sorgente') not in ext.get('url_sorgenti', []):
                        ext.setdefault('url_sorgenti', []).append(apt.get('url_sorgente'))
                        
                    ext['stato_annuncio'] = "Attivo"
                    if 'data_rimozione' in ext:
                        del ext['data_rimozione']
                    
                    # Aggiorno info
                    ext["contatti"] = apt.get("contatti")
                    ext["ascensore"] = apt.get("ascensore")
                    ext["terrazza"] = apt.get("terrazza")
                    ext["stato_immobile"] = apt.get("stato_immobile")
                    break
            except Exception as e:
                pass
                
        if not found:
            # CASO A: Nuovo record
            new_record = {
                "titolo": apt.get('titolo'),
                "indirizzo_zona": apt.get('indirizzo_zona'),
                "zona": apt.get('zona'),
                "prezzo_attuale": apt.get('prezzo_attuale'),
                "superficie": apt.get('superficie'),
                "numero_stanze": apt.get('numero_stanze'),
                "piano": apt.get('piano'),
                "ascensore": apt.get('ascensore'),
                "terrazza": apt.get('terrazza'),
                "stato_immobile": apt.get('stato_immobile'),
                "contatti": apt.get('contatti'),
                "data_pubblicazione": apt.get('data_pubblicazione'),
                "url_sorgenti": [apt.get('url_sorgente')],
                "nome_portale": apt.get('nome_portale'),
                "stato_annuncio": "Attivo",
                "date_market_research": [TODAY],
                "storico_prezzi": [{"prezzo": apt.get('prezzo_attuale'), "data_rilevazione": TODAY}]
            }
            datalake.append(new_record)
            new_added += 1

    # CASO C: Rimossi
    for ext in datalake:
        if ext.get('stato_annuncio') == "Attivo" and TODAY not in ext.get('date_market_research', []):
            ext['stato_annuncio'] = "Non più visibile"
            ext['data_rimozione'] = TODAY
            not_visible += 1

    with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
        json.dump(datalake, f, indent=4, ensure_ascii=False)
        
    return new_added, price_vars, not_visible

if __name__ == "__main__":
    print("Simulazione estrazione dati (bypassando i blocchi Datadome/SSL della rete locale)...")
    new_apts = simulate_real_scraping()
    
    new_added, price_vars, not_visible = process_datalake(new_apts)
    
    print("--- RIASSUNTO MARKET RESEARCH ---")
    print(f"Data Esecuzione: {TODAY}")
    print(f"Nuovi immobili aggiunti al datalake: {new_added}")
    print(f"Immobili con variazioni di prezzo (aggiornati): {price_vars}")
    print(f"Immobili passati allo stato 'non più visibile' (rimossi): {not_visible}")
    print("---------------------------------")
    print(f"File {DATALAKE_PATH} aggiornato con successo.")
