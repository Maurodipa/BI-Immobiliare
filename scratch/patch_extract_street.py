with open('scrape_idealista.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_target = """def extract_street(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico)\\s+([^,]+)', title, re.IGNORECASE)
    if match:
        return match.group(0).strip().lower()
    return \"\""""

new_replacement = """def extract_street(title):
    match = re.search(r'(via|viale|piazza|largo|corso|vicolo|vico|arco|salita|rampa)\\s+([^,]+)', title, re.IGNORECASE)
    if match:
        street = match.group(0).strip().lower()
        street = re.sub(r'\\s+s\\.n\\.c|\\s+\\d+.*$', '', street, flags=re.IGNORECASE).strip()
        return street
    m_in = re.search(r'in\\s+([A-Za-zÀ-ÿ\\s\\\'-]+?)(?:,\\s*\\d+)?,\\s*[^,]+,\\s*Roma', title, re.IGNORECASE)
    if m_in:
        candidate = m_in.group(1).strip().lower()
        if candidate not in ["vendita", "affitto", "asta"]:
            return candidate
    return \"\""""

content = content.replace(old_target.replace('\r\n', '\n'), new_replacement.replace('\r\n', '\n'))
content = content.replace(old_target, new_replacement)

with open('scrape_idealista.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("scrape_idealista.py patched successfully")
