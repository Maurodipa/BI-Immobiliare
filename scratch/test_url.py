from seleniumbase import SB
import time
with SB(uc=True, headless=True) as sb:
    url = 'https://www.idealista.it/aree/vendita-case/con-prezzo_600000,bilocali-2,trilocali-3,quadrilocali-4,5-locali-o-piu/lista-mappa?shape=%28%28umv%7EFyiakAmG%7DAqDcOqDeXsFcSqF%7BDkKh%40kL%60GkK%7CE_Dw%5C%7EDoFjOgQ%7CG_J%7EIwBvKaKrIqCpLfFpIrH%7EBvTpJjHdRfJr%40jKGnJ%7DClH_SzZcVjS%29%29'
    sb.open(url)
    time.sleep(3)
    try:
        href = sb.get_attribute('a.icon-list-items', 'href')
        print('URL LISTA:', href)
    except Exception as e:
        print('Errore', e)
