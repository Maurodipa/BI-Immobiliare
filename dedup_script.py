import json
import re

DATALAKE_PATH = "datalake_poligono.json"

def normalize_street(title):
    # Estrai la via come facevamo prima
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico)\s+([^,]+)', title, re.IGNORECASE)
    if not match:
        return ""
    
    street = match.group(0).lower().strip()
    
    # Rimuoviamo articoli e preposizioni
    words_to_remove = [" di ", " del ", " dello ", " della ", " dei ", " degli ", " delle ", " da ", " in "]
    for w in words_to_remove:
        street = street.replace(w, " ")
        
    # Sostituzioni numeri in lettere
    num_map = {
        "uno": "1", "due": "2", "tre": "3", "quattro": "4", 
        "cinque": "5", "sei": "6", "sette": "7", "otto": "8", 
        "nove": "9", "dieci": "10", "undici": "11", "dodici": "12",
        "venti": "20", "ventiquattro": "24", "venticinque": "25", "xx ": "20 "
    }
    for word, num in num_map.items():
        street = re.sub(rf'\b{word}\b', num, street)
        
    # Rimuoviamo spazi multipli
    street = re.sub(r'\s+', ' ', street).strip()
    return street

with open(DATALAKE_PATH, "r", encoding="utf-8") as f:
    datalake = json.load(f)

# Raggruppiamo gli attivi per chiave di deduplicazione
unique_map = {}
cleaned_datalake = []

for item in datalake:
    if item.get("stato_annuncio") != "Attivo":
        cleaned_datalake.append(item)
        continue
        
    title = item.get("titolo", "")
    street_norm = normalize_street(title)
    
    # Chiave = via_normalizzata + stanze + superficie
    stanze = str(item.get("numero_stanze", ""))
    sup = str(item.get("superficie", ""))
    
    key = f"{street_norm}_{stanze}_{sup}"
    
    if key in unique_map:
        # Trovato duplicato, facciamo merge degli URL e teniamo il prezzo più basso
        existing = unique_map[key]
        
        # Uniamo gli URL sorgenti
        for url in item.get("url_sorgenti", []):
            if url not in existing["url_sorgenti"]:
                existing["url_sorgenti"].append(url)
                
        # Aggiorniamo il prezzo se quello nuovo è più basso
        if item.get("prezzo_attuale", float('inf')) < existing.get("prezzo_attuale", 0):
            existing["prezzo_attuale"] = item["prezzo_attuale"]
            
        print(f"MERGED:\n1. {existing['titolo']}\n2. {title}\n(Key: {key})\n")
    else:
        unique_map[key] = item

# Aggiungiamo i deduplicati al datalake pulito
cleaned_datalake.extend(unique_map.values())

with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
    json.dump(cleaned_datalake, f, indent=4)

print(f"Deduplicazione completata. Elementi totali: {len(cleaned_datalake)}")
