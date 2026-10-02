import json
import os
from scrape_real import scrape, process_datalake

# Carichiamo solo i 3 test di partenza se presenti
DATALAKE_PATH = "datalake_roma.json"
initial_test_items = []

if os.path.exists(DATALAKE_PATH):
    with open(DATALAKE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            if item.get("stato_annuncio") == "Non più visibile":
                initial_test_items.append(item)

# Scriviamo temporaneamente solo i 3 test iniziali
with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
    json.dump(initial_test_items, f, indent=4, ensure_ascii=False)

print("Esecuzione scraping con le nuove regole di deduplicazione per via...")
apts = scrape()
print(f"Estratti {len(apts)} annunci. Processamento datalake...")
process_datalake(apts)
print("Datalake rigenerato con successo!")
