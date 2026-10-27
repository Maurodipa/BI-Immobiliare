from seleniumbase import SB

url = "https://www.immobiliare.it/vendita-case/roma/?prezzoMassimo=700000&localiMinimo=2"

with SB(uc=True, test=True, locale_code="it") as sb:
    sb.activate_cdp_mode(url)
    sb.sleep(3)
    src = sb.get_page_source()
    print("CDP mode length:", len(src))
    print("Contains captcha-delivery?", "captcha-delivery" in src)
    print("Contains ListItem_item?", "ListItem_item" in src or "Property_card" in src)
