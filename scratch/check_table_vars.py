import sys
sys.path.append('.')
import json
import dump_table_v4 as dt
sys.stdout.reconfigure(encoding='utf-8')

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

attivi = [d for d in data if d.get('stato_annuncio') == 'Attivo' and not dt.is_c1_c2(d.get('titolo', '')) and not dt.is_asta(d)]
attivi = dt.deduplicate_group(attivi)
attivi.sort(key=dt.get_sort_key)

print(f"Attivi deduplicati: {len(attivi)}")
for i, item in enumerate(attivi, 1):
    var = dt.get_price_variation(item)
    if var != "-":
        print(f"{i}. {item['titolo'][:50]} | Prezzo: {item.get('prezzo_attuale')} | Var: {var}")
