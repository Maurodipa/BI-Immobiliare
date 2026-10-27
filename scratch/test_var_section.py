import sys
sys.path.append('.')
import json
import dump_table_v4 as dt
sys.stdout.reconfigure(encoding='utf-8')

with open('datalake_poligono.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

attivi = [d for d in data if d.get('stato_annuncio') == 'Attivo' and not dt.is_c1_c2(d.get('titolo', '')) and not dt.is_asta(d)]
attivi = dt.deduplicate_group(attivi)

con_variazioni = [item for item in attivi if dt.get_price_variation(item) != "-"]
print(f"Totale con variazioni tra gli attivi: {len(con_variazioni)}")

for item in con_variazioni:
    print(item['titolo'][:45], "->", dt.get_price_variation(item))
