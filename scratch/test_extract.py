import json
import re

data = json.load(open('datalake_poligono.json', encoding='utf-8'))

def extract_query(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico)\s+([^,-]+)', title, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    
    match = re.search(r' a ([A-Z][a-zA-Z\s]+)', title)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'in zona ([A-Z][a-zA-Z\s]+)', title)
    if match:
        return match.group(1).strip()
    return None

for d in data:
    if d.get('nome_portale') == 'engelvoelkers.com':
        t = d.get('titolo')
        print(f"Title: {t}")
        print(f"Query: {extract_query(t)}")
        print("-")
