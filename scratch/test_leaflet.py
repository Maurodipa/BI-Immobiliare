from playwright.sync_api import sync_playwright

html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { width: 1000px; height: 800px; }
        body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([41.898, 12.475], 14);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);
    </script>
</body>
</html>
"""

with open("scratch/leaflet_test.html", "w", encoding="utf-8") as f:
    f.write(html)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1000, "height": 800})
    page.goto(f"file:///{__file__.replace('\\\\', '/').replace('test_leaflet.py', 'leaflet_test.html')}")
    page.wait_for_timeout(4000)
    page.screenshot(path="scratch/leaflet_map.png")
    browser.close()

print("Leaflet screenshot OK")
