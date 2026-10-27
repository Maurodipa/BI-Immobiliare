import numpy as np

# Punti SVG estratti dal path dell'utente:
# d="M-1266 230L-1388 304L-1348 440L-1261 421L-1151 591L-1199 669L-915 884L-697 874L-614 716L-779 645L-886 613L-1003 518z"
svg_pts = [
    (-1266, 230),  # 0: Top X (Via della Lungara / Ponte Mazzini)
    (-1388, 304),  # 1: NW corner (Via delle Mantellate)
    (-1348, 440),  # 2: West Mantellate / San Francesco di Sales
    (-1261, 421),  # 3: Gran Farina Cooking School (Via dei Riari)
    (-1151, 591),  # 4: Orto Botanico / Via Corsini
    (-1199, 669),  # 5: Giardino Domenico Bonamini
    (-915, 884),   # 6: Sud-Ovest (Via Mameli / Via della Luce)
    (-697, 874),   # 7: Sud-Est (Istituto Istruzione Sup. / Via Anicia)
    (-614, 716),   # 8: Ponte Palatino
    (-779, 645),   # 9: Isola Tiberina / Ponte Fabricio
    (-886, 613),   # 10: Ponte Garibaldi / Ponte Sisto
    (-1003, 518),  # 11: Lungotevere della Farnesina
]

# Punti di calibrazione noti dall'immagine:
# 1. Ponte Palatino: pt 8 = (-614, 716) -> (Lat: 41.88914, Lon: 12.47920)
# 2. Giardino Domenico Bonamini: pt 5 = (-1199, 669) -> (Lat: 41.88950, Lon: 12.46511)
# 3. Top X (Via della Lungara / Lungotevere Gianicolense): pt 0 = (-1266, 230) -> (Lat: 41.89660, Lon: 12.46460)
# 4. Sud (Via Anicia / Istituto Sup.): pt 7 = (-697, 874) -> (Lat: 41.88560, Lon: 12.47720)

calib_svg = np.array([
    [-614, 716, 1],   # Ponte Palatino
    [-1199, 669, 1],  # Bonamini
    [-1266, 230, 1],  # Top X
    [-697, 874, 1]    # Via Anicia / Ist. Sup.
])

# Coordinate note (Lon, Lat)
calib_lon = np.array([12.47920, 12.46511, 12.46460, 12.47720])
calib_lat = np.array([41.88914, 41.88950, 41.89660, 41.88560])

# Risoluzione minimi quadrati
coeff_lon, _, _, _ = np.linalg.lstsq(calib_svg, calib_lon, rcond=None)
coeff_lat, _, _, _ = np.linalg.lstsq(calib_svg, calib_lat, rcond=None)

print("Coefficienti Lon:", coeff_lon)
print("Coefficienti Lat:", coeff_lat)

print("\n--- Coordinate calcolate per tutti i 12 punti ---")
computed_pts = []
for idx, (x, y) in enumerate(svg_pts):
    lon = coeff_lon[0]*x + coeff_lon[1]*y + coeff_lon[2]
    lat = coeff_lat[0]*x + coeff_lat[1]*y + coeff_lat[2]
    computed_pts.append((lat, lon))
    print(f"Punto {idx+1:2d} (SVG: {x:5d}, {y:4d}) -> Lat: {lat:.6f}, Lon: {lon:.6f}")

print("\nFormato stringa poligono Trastevere:")
poly_str = ";".join([f"{lat:.6f},{lon:.6f}" for lat, lon in computed_pts])
print(poly_str)
