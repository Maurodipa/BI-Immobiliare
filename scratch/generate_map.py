import json
import os
from playwright.sync_api import sync_playwright

# 1. Poligono Attuale Centro Storico (quello con Tridente, Navona, Pantheon, Spagna, Trevi)
poly_attuale = [
    [41.90151, 12.469482],
    [41.900999, 12.464333],
    [41.899338, 12.463818],
    [41.894994, 12.467766],
    [41.891799, 12.472057],
    [41.890777, 12.47901],
    [41.892758, 12.481842],
    [41.895377, 12.482786],
    [41.896655, 12.486477],
    [41.898188, 12.490211],
    [41.900297, 12.492571],
    [41.902149, 12.490854],
    [41.903108, 12.488923],
    [41.90413, 12.487507],
    [41.905982, 12.48313],
    [41.911763, 12.477207],
    [41.910741, 12.472959],
    [41.905599, 12.475147],
    [41.90151, 12.469482]
]

# 2. Poligono ESATTO di Trastevere disegnato dall'utente (estratto dal path SVG):
# d="M-1266 230L-1388 304L-1348 440L-1261 421L-1151 591L-1199 669L-915 884L-697 874L-614 716L-779 645L-886 613L-1003 518z"
poly_trastevere_utente = [
    [41.896763, 12.464525],  # 1: Inizio Via della Lungara / Ponte Mazzini (punto con la X)
    [41.895420, 12.461398],  # 2: Via delle Mantellate ovest
    [41.893106, 12.462082],  # 3: Via dei Riari ovest / Buon Pastore
    [41.893483, 12.464240],  # 4: Gran Farina Cooking School
    [41.890626, 12.466556],  # 5: Orto Botanico / Via Corsini
    [41.889258, 12.465221],  # 6: Giardino Domenico Bonamini / sopra Vicolo del Cedro
    [41.885729, 12.471676],  # 7: Angolo Sud-Ovest (Via Mameli / Via della Luce)
    [41.886028, 12.477003],  # 8: Angolo Sud-Est (Istituto Statale Istruzione Superiore / Via Anicia)
    [41.888791, 12.479360],  # 9: Ponte Palatino
    [41.889915, 12.475495],  # 10: Lungotevere Anguillara / fronte Isola Tiberina
    [41.890403, 12.472959],  # 11: Ponte Garibaldi / Ponte Sisto
    [41.891967, 12.470313],  # 12: Piazza Trilussa / Lungotevere Farnesina
    [41.896763, 12.464525]   # Chiusura al punto 1
]

# 3. Poligono Unificato che fonde il Centro Storico + il poligono esatto dell'utente:
poly_unificato = [
    # Nord Centro Storico
    [41.911763, 12.477207],  # Piazza del Popolo
    [41.910741, 12.472959],  # Ponte Margherita
    [41.905599, 12.475147],  # Porto di Ripetta
    [41.901510, 12.469482],  # Ponte Umberto I
    [41.900999, 12.464333],  # Ponte Sant'Angelo
    [41.899338, 12.463818],  # Ponte Vittorio Emanuele II
    # ATTRAVERSAMENTO SUL POLIGONO ESATTO DELL'UTENTE (Riva Ovest)
    [41.896763, 12.464525],  # 1: Via della Lungara (X dell'immagine)
    [41.895420, 12.461398],  # 2: Via delle Mantellate
    [41.893106, 12.462082],  # 3: Via dei Riari
    [41.893483, 12.464240],  # 4: Gran Farina Cooking School
    [41.890626, 12.466556],  # 5: Orto Botanico
    [41.889258, 12.465221],  # 6: Giardino Domenico Bonamini
    [41.885729, 12.471676],  # 7: Via Mameli / Luce
    [41.886028, 12.477003],  # 8: Istituto Superiore / Via Anicia
    [41.888791, 12.479360],  # 9: Ponte Palatino
    # RIENTRO NEL CENTRO STORICO MONUMENTALE (Riva Est)
    [41.890777, 12.479010],  # Isola Tiberina / Ghetto
    [41.892758, 12.481842],  # Teatro di Marcello
    [41.895377, 12.482786],  # Largo Argentina
    [41.896655, 12.486477],  # Fontana di Trevi / Corso
    [41.898188, 12.490211],  # Quirinale
    [41.900297, 12.492571],  # Piazza Barberini
    [41.902149, 12.490854],  # Via Veneto
    [41.903108, 12.488923],  # Via Sistina
    [41.904130, 12.487507],  # Trinità dei Monti
    [41.905982, 12.483130],  # Piazza di Spagna
    [41.911763, 12.477207]   # Chiusura
]

unificato_str = ";".join([f"{lat:.6f},{lon:.6f}" for lat, lon in poly_unificato])

html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8" />
    <title>Mappa Poligono Roma Centro + Trastevere Utente</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        #map {{ width: 100%; height: 100%; background: #e5e3df; }}
        .info-card {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(8px);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px 22px;
            max-width: 420px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge-user {{ background: #eff6ff; color: #0284c7; border: 1px solid #bae6fd; }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-top: 10px;
            font-size: 13px;
            color: #334155;
        }}
        .legend-color {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            margin-right: 10px;
            flex-shrink: 0;
        }}
        .btn {{
            cursor: pointer;
            border: none;
            padding: 7px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            margin-top: 6px;
            margin-right: 4px;
        }}
        .btn-primary {{ background: #2563eb; color: #fff; }}
        .btn-secondary {{ background: #0284c7; color: #fff; }}
        .btn-purple {{ background: #7c3aed; color: #fff; }}
        .btn-neutral {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
    </style>
</head>
<body>
    <div id="map"></div>

    <div class="info-card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <h2 style="margin: 0; font-size: 18px; color: #0f172a; font-weight: 700;">Poligono con Trastevere</h2>
            <span class="badge badge-user">DISEGNO UTENTE</span>
        </div>
        <p style="margin: 0 0 12px 0; font-size: 13px; color: #64748b; line-height: 1.4;">
            Rappresentazione fedele del poligono tracciato nella tua immagine (coordinate SVG calibrate su OSM) unito al perimetro del Centro Storico / Tridente.
        </p>

        <div class="legend-item">
            <div class="legend-color" style="background: rgba(37, 99, 235, 0.22); border: 2.5px solid #2563eb;"></div>
            <div><strong>Poligono Iniziale (Tridente & Centro)</strong></div>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(2, 132, 199, 0.25); border: 2.5px solid #0074c1;"></div>
            <div><strong>Nuova Zona Trastevere (Tua Immagine)</strong></div>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ef4444; border-radius: 50%; width: 14px; height: 14px; border: 2px solid #fff; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>
            <div><strong>Bilocale Vicolo del Cedro</strong> (€ 490k - <span style="color: #0284c7; font-weight: bold;">INCLUSO</span>)</div>
        </div>

        <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid #e2e8f0;">
            <div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px;">Visualizzazione:</div>
            <button class="btn btn-primary" onclick="showBoth()">Mostra Entrambi</button>
            <button class="btn btn-purple" onclick="showUnified()">Poligono Unificato</button>
            <button class="btn btn-neutral" onclick="focusCedro()">Zoom Vicolo del Cedro</button>
        </div>
    </div>

    <script>
        var map = L.map('map', {{
            zoomControl: true
        }}).setView([41.8955, 12.4740], 14);

        L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var coordsAttuale = {json.dumps(poly_attuale)};
        var coordsTrastevere = {json.dumps(poly_trastevere_utente)};
        var coordsUnificato = {json.dumps(poly_unificato)};

        // Layer 1: Attuale
        var layerAttuale = L.polygon(coordsAttuale, {{
            color: '#2563eb',
            weight: 3.5,
            fillColor: '#3b82f6',
            fillOpacity: 0.18
        }}).addTo(map);
        layerAttuale.bindTooltip("<b>Poligono Iniziale</b><br>Centro Storico / Tridente", {{sticky: true}});

        // Layer 2: Trastevere Utente (colore esatto #0074c1 dal path fornito)
        var layerTrastevere = L.polygon(coordsTrastevere, {{
            color: '#0074c1',
            weight: 3.5,
            fillColor: '#0074c1',
            fillOpacity: 0.28
        }}).addTo(map);
        layerTrastevere.bindTooltip("<b>Zona Trastevere richiesta</b><br>Piazza Trilussa / Santa Maria / Lungara", {{sticky: true}});

        // Mostra i singoli vertici del poligono dell'utente come cerchietti bianchi con bordo blu (come nello screenshot!)
        coordsTrastevere.slice(0, -1).forEach(function(pt, idx) {{
            L.circleMarker(pt, {{
                radius: 5,
                fillColor: '#ffffff',
                color: '#0074c1',
                weight: 2,
                opacity: 1,
                fillOpacity: 1
            }}).addTo(map);
        }});

        // Layer 3: Unificato
        var layerUnificato = L.polygon(coordsUnificato, {{
            color: '#7c3aed',
            weight: 4,
            fillColor: '#8b5cf6',
            fillOpacity: 0.25
        }});
        layerUnificato.bindTooltip("<b>Nuovo Poligono Unificato Finale</b><br>Centro Storico + Trastevere", {{sticky: true}});

        // Marker Vicolo del Cedro
        var cedroMarker = L.circleMarker([41.8903, 12.4685], {{
            radius: 8,
            fillColor: '#ef4444',
            color: '#ffffff',
            weight: 2.5,
            opacity: 1,
            fillOpacity: 0.95
        }}).addTo(map);

        cedroMarker.bindPopup(`
            <div style="font-family: inherit; font-size: 13px;">
                <b style="color: #b91c1c;">Bilocale Vicolo del Cedro</b><br>
                <b>Prezzo:</b> € 490.000<br>
                <b>Superficie:</b> 60 mq · 2° piano<br>
                <div style="margin-top: 6px; font-size: 11px; padding: 4px 6px; background: #eff6ff; border: 1px solid #bae6fd; border-radius: 4px; color: #0369a1;">
                    ✅ <b>Pienamente compreso nella zona disegnata</b>
                </div>
            </div>
        `).openPopup();

        // Punti di riferimento principali
        var landmarks = [
            {{ name: "Piazza del Popolo", pos: [41.9109, 12.4764] }},
            {{ name: "Piazza di Spagna", pos: [41.9059, 12.4827] }},
            {{ name: "Pantheon", pos: [41.8986, 12.4769] }},
            {{ name: "Piazza Navona", pos: [41.8992, 12.4731] }},
            {{ name: "Ponte Mazzini", pos: [41.8960, 12.4660] }},
            {{ name: "Piazza Trilussa", pos: [41.8922, 12.4705] }},
            {{ name: "S. Maria in Trastevere", pos: [41.8894, 12.4701] }},
            {{ name: "Ponte Palatino", pos: [41.8891, 12.4792] }}
        ];

        landmarks.forEach(function(lm) {{
            L.circleMarker(lm.pos, {{
                radius: 4,
                fillColor: '#0f172a',
                color: '#ffffff',
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.7
            }}).addTo(map).bindTooltip(lm.name, {{ permanent: false, direction: 'top', offset: [0, -5] }});
        }});

        function showBoth() {{
            map.removeLayer(layerUnificato);
            map.addLayer(layerAttuale);
            map.addLayer(layerTrastevere);
            map.fitBounds(layerAttuale.getBounds().extend(layerTrastevere.getBounds()), {{ padding: [30, 30] }});
        }}

        function showUnified() {{
            map.removeLayer(layerAttuale);
            map.removeLayer(layerTrastevere);
            map.addLayer(layerUnificato);
            map.fitBounds(layerUnificato.getBounds(), {{ padding: [30, 30] }});
        }}

        function focusCedro() {{
            map.setView([41.8903, 12.4685], 16);
            cedroMarker.openPopup();
        }}
    </script>
</body>
</html>
"""

html_path = "scratch/mappa_trastevere.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML salvato in {html_path}")

img_dest = r"C:\Users\mauro\.gemini\antigravity\brain\175b7fe0-188c-4061-a9c8-745b4b82a986\mappa_poligono_trastevere.png"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    abs_html = os.path.abspath(html_path).replace("\\", "/")
    page.goto(f"file:///{abs_html}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    page.screenshot(path=img_dest)
    browser.close()

print(f"Screenshot generato in: {img_dest}")
