import json
import re

DATALAKE_PATH = "datalake_roma.json"

def extract_street(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico|corso)\s+([^,]+)', title, re.IGNORECASE)
    if match:
        return match.group(0).strip().lower()
    return ""

with open(DATALAKE_PATH, "r", encoding="utf-8") as f:
    datalake = json.load(f)

new_dl = []
merged_count = 0

for apt in datalake:
    found = False
    for ext in new_dl:
        via_ext = extract_street(ext.get('titolo', ''))
        via_apt = extract_street(apt.get('titolo', ''))
        
        stessa_via = False
        if via_ext and via_apt and via_ext == via_apt:
            stessa_via = True
        else:
            stessa_via = (ext.get('indirizzo_zona', '').lower() == apt.get('indirizzo_zona', '').lower()) or \
                         (apt.get('indirizzo_zona', '').lower() in ext.get('titolo', '').lower()) or \
                         (ext.get('indirizzo_zona', '').lower() in apt.get('titolo', '').lower())

        if (stessa_via and
            ext.get('zona') == apt.get('zona') and
            str(ext.get('piano')) == str(apt.get('piano')) and
            str(ext.get('numero_stanze')) == str(apt.get('numero_stanze')) and
            abs(int(ext.get('superficie', 0)) - int(apt.get('superficie', 0))) <= 5):
            
            # Uniamo
            found = True
            for u in apt.get('url_sorgenti', []):
                if u not in ext.get('url_sorgenti', []):
                    ext['url_sorgenti'].append(u)
            
            # Prendiamo il prezzo più recente se diverso
            if apt.get('prezzo_attuale') != ext.get('prezzo_attuale'):
                ext['storico_prezzi'].append({"prezzo": apt.get('prezzo_attuale'), "data_rilevazione": "2026-10-02"})
                ext['prezzo_attuale'] = apt.get('prezzo_attuale')
            merged_count += 1
            break
            
    if not found:
        new_dl.append(apt)

with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
    json.dump(new_dl, f, indent=4, ensure_ascii=False)

print(f"Unificati {merged_count} annunci.")
