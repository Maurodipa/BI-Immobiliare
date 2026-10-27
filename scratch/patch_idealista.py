with open('scrape_idealista.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if 'if "captcha-delivery" in html or "DataDome" in html' in line:
        new_lines.append('                if "captcha-delivery" in html or "DataDome" in html or len(html) < 5000:\n')
        new_lines.append('                    print("   [!] DataDome rilevato su Idealista. Tentativo di bypass automatico...")\n')
        new_lines.append('                    try:\n')
        new_lines.append('                        sb.uc_gui_click_captcha()\n')
        new_lines.append('                        time.sleep(4)\n')
        new_lines.append('                    except Exception:\n')
        new_lines.append('                        pass\n')
        new_lines.append('                    try:\n')
        new_lines.append('                        sb.uc_gui_handle_captcha()\n')
        new_lines.append('                        time.sleep(4)\n')
        new_lines.append('                    except Exception:\n')
        new_lines.append('                        pass\n')
        new_lines.append('                    html = sb.get_page_source()\n')
        new_lines.append('\n')
        new_lines.append('                if "captcha-delivery" in html or "DataDome" in html or len(html) < 5000:\n')
        new_lines.append('                    print("   [!] Idealista bloccato da DataDome. Passo oltre per non bloccare gli altri portali.")\n')
        new_lines.append('                    break\n')
        skip = True
    elif skip and '# Prova a chiudere cookie banner' in line:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('scrape_idealista.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Aggiornato scrape_idealista.py con successo")
