"""
Script one-shot: rimuove dal datalake gli annunci E&V
che non passano il nuovo filtro zona verde/rossa.
"""
import json
import sys
import os

# ── stesso filtro di scrape_ev.py ────────────────────────────────────
ZONE_VERDI = [
    "centro storico", "centro", "tridente",
    "spagna", "trevi", "colonna", "campo marzio",
    "ponte", "parione", "regola",
    "sant eustachio", "sant'eustachio",
    "pantheon", "pigna", "trastevere",
]

ZONE_ROSSE = [
    "monti", "campitelli", "sant'angelo", "sant angelo",
    "ripa", "borgo", "esquilino", "ludovisi",
    "sallustiano", "castro pretorio", "celio",
    "testaccio", "san saba", "prati",
    "pigneto", "nomentano", "tuscolano", "quadraro",
    "san giovanni", "appio", "bologna", "policlinico",
    "furio camillo", "re di roma", "colle oppio",
    "conca d'oro", "valli", "citta giardino", "tufello",
    "pantano", "ostia", "eur", "tiburtino", "prenestino",
    "parioli", "flaminio", "salario", "trionfale",
    "aurelio", "gianicolense", "portuense", "ostiense",
]

def zone_ammessa(zona: str) -> bool:
    z = zona.lower()
    for parola in ZONE_ROSSE:
        if parola in z:
            return False
    for parola in ZONE_VERDI:
        if parola in z:
            return True
    return True  # generica → includi

# ── Pulizia datalake ─────────────────────────────────────────────────
DATALAKE_PATH = "datalake_poligono.json"
with open(DATALAKE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

rimossi = []
rimasti = []
for d in data:
    if d.get("nome_portale") == "engelvoelkers.com":
        zona = d.get("indirizzo_zona", "Roma")
        if not zone_ammessa(zona):
            rimossi.append(d)
            print(f"  RIMOSSO: {zona} | {d.get('titolo', '')[:60]}")
            continue
    rimasti.append(d)

with open(DATALAKE_PATH, "w", encoding="utf-8") as f:
    json.dump(rimasti, f, indent=4, ensure_ascii=False)

print(f"\nRimossi: {len(rimossi)}")
print(f"Rimasti nel datalake: {len(rimasti)}")
