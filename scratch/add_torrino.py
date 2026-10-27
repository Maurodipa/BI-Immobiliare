import glob

def append_torrino(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'ZONE_ROSSE = [' in content and 'torrino' not in content.lower():
        new_content = content.replace('ZONE_ROSSE = [', 'ZONE_ROSSE = [\n    "torrino",', 1)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Added torrino to {filepath}')

for py_file in glob.glob('*.py') + glob.glob('scratch/*.py'):
    if 'scrape_' in py_file or 'clean_' in py_file:
        append_torrino(py_file)
