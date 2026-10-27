import urllib.request
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request('https://www.immobiliare.it/annunci/133856720/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        title_m = re.search(r'<title>(.*?)</title>', html)
        print('Title:', title_m.group(1) if title_m else 'No title')
        
        # Check text snippet
        m_desc = re.search(r'<div class="[^"]*description[^"]*">(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
        if m_desc:
            print('Description snippet:', m_desc.group(1)[:400])
        else:
            # strip tags from body
            clean = re.sub(r'<[^>]+>', ' ', html)
            clean = re.sub(r'\s+', ' ', clean)
            print('Clean snippet:', clean[:400])
except Exception as e:
    print('Error:', e)
