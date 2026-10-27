# 🗺️ Report Poligono Aggiornato: Centro Storico & Trastevere (Disegno Utente)

Il presente report documenta la corretta georeferenziazione e integrazione del poligono disegnato a mano su mappa Leaflet (`<path d="M-1266 230L-1388 304..."></path>`) con il **poligono iniziale del Tridente e Centro Storico**.

La mappa interattiva di verifica è consultabile in **[`mappa_interattiva_trastevere.html`](file:///C:/Users/mauro/.gemini/antigravity/brain/175b7fe0-188c-4061-a9c8-745b4b82a986/mappa_interattiva_trastevere.html)**.

---

## 📍 Mappa del Nuovo Perimetro Unificato

Di seguito la vista del perimetro unificato continuo che copre sia il Tridente / Centro Storico, sia la zona nobile di Trastevere:

![Poligono Unificato Finale](C:/Users/mauro/.gemini/antigravity/brain/175b7fe0-188c-4061-a9c8-745b4b82a986/mappa_poligono_unificato.png)

### 🔍 Dettaglio Vertici Trastevere (Disegno Utente)

Visualizzazione ravvicinata della zona Trastevere con i **12 vertici calibrati** coincidenti con i punti di ancoraggio del disegno originale:

![Dettaglio Vertici Trastevere](C:/Users/mauro/.gemini/antigravity/brain/175b7fe0-188c-4061-a9c8-745b4b82a986/mappa_dettaglio_trastevere.png)

> [!TIP]
> Per interagire con la mappa (zoomare su singole vie, accendere/spegnere i singoli livelli e verificare il Bilocale di Vicolo del Cedro), puoi aprire direttamente nel browser la **[Mappa Interattiva (HTML)](file:///C:/Users/mauro/.gemini/antigravity/brain/175b7fe0-188c-4061-a9c8-745b4b82a986/mappa_interattiva_trastevere.html)**.

---

## 📐 Tabella di Verifica dei 12 Vertici di Trastevere

I vertici estratti dalla stringa SVG `<path d="M-1266 230L-1388 304L-1348 440L-1261 421L-1151 591L-1199 669L-915 884L-697 874L-614 716L-779 645L-886 613L-1003 518z">` sono stati convertiti nelle coordinate WGS84 verificate:

| # | Punto SVG | Latitudine | Longitudine | Riferimento Topografico / Stradale | Note di Delimitazione |
|---|---|---|---|---|---|
| **1** | `(-1266, 230)` | `41.896763` | `12.464525` | **Via della Lungara** (altezza Ponte Mazzini) | Vertice iniziale e finale con la **`X`** blu |
| **2** | `(-1388, 304)` | `41.895420` | `12.461398` | **Via delle Mantellate** (ovest) | Bordo carcere Regina Coeli |
| **3** | `(-1348, 440)` | `41.893106` | `12.462082` | **Via dei Riari** (ovest / Buon Pastore) | Bordo pedemontano Gianicolo |
| **4** | `(-1261, 421)` | `41.893483` | `12.464240` | **Via dei Riari** (Gran Farina Cooking School) | Rientro verso l'interno di Trastevere |
| **5** | `(-1151, 591)` | `41.890626` | `12.466556` | **Orto Botanico / Via Corsini** | Bordo giardini storici |
| **6** | `(-1199, 669)` | `41.889258` | `12.465221` | **Giardino Domenico Bonamini** | Monte sopra Vicolo del Cedro |
| **7** | `(-915, 884)` | `41.885729` | `12.471676` | **Via Goffredo Mameli / Via della Luce** | Limite Sud-Ovest (taglia fuori Porta Portese) |
| **8** | `(-697, 874)` | `41.886028` | `12.477003` | **Via Anicia** (Ist. Superiore Statale) | Limite Sud-Est (esclude Trastevere Bassa) |
| **9** | `(-614, 716)` | `41.888791` | `12.479360` | **Ponte Palatino** | Connessione su Tevere / Bocca della Verità |
| **10**| `(-779, 645)` | `41.889915` | `12.475495` | **Lungotevere degli Anguillara** | Sponda ovest di fronte a Isola Tiberina |
| **11**| `(-886, 613)` | `41.890403` | `12.472959` | **Ponte Garibaldi / Ponte Sisto** | Sponda ovest Tevere |
| **12**| `(-1003, 518)`| `41.891967` | `12.470313` | **Piazza Trilussa / Lungotevere Farnesina** | Rientro verso Via della Lungara |

---

## 💻 Stringa Coordinate del Poligono Unificato

Unendo i vertici perimetrali esterni del **Centro Storico / Tridente** con i vertici della **zona Trastevere dell'utente**, si ottiene un perimetro continuo privo di auto-intersezioni composto da 26 punti:

```python
POLYGON = "41.911763,12.477207;41.910741,12.472959;41.905599,12.475147;41.901510,12.469482;41.900999,12.464333;41.899338,12.463818;41.896763,12.464525;41.895420,12.461398;41.893106,12.462082;41.893483,12.464240;41.890626,12.466556;41.889258,12.465221;41.885729,12.471676;41.886028,12.477003;41.888791,12.479360;41.890777,12.479010;41.892758,12.481842;41.895377,12.482786;41.896655,12.486477;41.898188,12.490211;41.900297,12.492571;41.902149,12.490854;41.903108,12.488923;41.904130,12.487507;41.905982,12.483130;41.911763,12.477207"
```

### Parametro URL per Ricerca su Immobiliare.it (`vrt`)
```
41.911763%2C12.477207%3B41.910741%2C12.472959%3B41.905599%2C12.475147%3B41.901510%2C12.469482%3B41.900999%2C12.464333%3B41.899338%2C12.463818%3B41.896763%2C12.464525%3B41.895420%2C12.461398%3B41.893106%2C12.462082%3B41.893483%2C12.464240%3B41.890626%2C12.466556%3B41.889258%2C12.465221%3B41.885729%2C12.471676%3B41.886028%2C12.477003%3B41.888791%2C12.479360%3B41.890777%2C12.479010%3B41.892758%2C12.481842%3B41.895377%2C12.482786%3B41.896655%2C12.486477%3B41.898188%2C12.490211%3B41.900297%2C12.492571%3B41.902149%2C12.490854%3B41.903108%2C12.488923%3B41.904130%2C12.487507%3B41.905982%2C12.483130%3B41.911763%2C12.477207
```

---

## 🛠️ Modifiche Necessarie agli Script degli Scraper

Prima di rilanciare le ricerche automatiche, vanno applicate le seguenti configurazioni:

1. **`scrape_immobiliare.py`**:
   - Sostituire la costante `POLYGON` con la nuova stringa unificata.
   - Aggiornare il parametro `vrt` nell'`url_base`.
   - Aggiungere `"trastevere"` alla lista `ZONE_VERDI`.

2. **`scrape_ev.py`** (Engel & Völkers):
   - Sostituire la costante `POLYGON`.
   - Rimuovere `"trastevere"` da `ZONE_ROSSE` e aggiungerla alle zone autorizzate.

3. **`scrape_idealista.py`**:
   - Sostituire la costante `POLYGON`.
   - Rimuovere `"trastevere"` dalle parole chiave di scarto.
