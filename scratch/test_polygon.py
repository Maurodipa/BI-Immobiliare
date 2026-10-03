polygon_str = "41.90151,12.469482;41.900999,12.464333;41.899338,12.463818;41.894994,12.467766;41.891799,12.472057;41.890777,12.47901;41.892758,12.481842;41.895377,12.482786;41.896655,12.486477;41.898188,12.490211;41.900297,12.492571;41.902149,12.490854;41.903108,12.488923;41.90413,12.487507;41.905982,12.48313;41.911763,12.477207;41.910741,12.472959;41.905599,12.475147;41.90151,12.469482"

def is_point_in_polygon(lat, lon, polygon_str):
    coords = []
    for pair in polygon_str.split(';'):
        if pair.strip():
            lat_p, lon_p = map(float, pair.split(','))
            coords.append((lat_p, lon_p))
            
    x, y = lon, lat
    n = len(coords)
    inside = False
    
    p1x, p1y = coords[0][1], coords[0][0]
    for i in range(n + 1):
        p2x, p2y = coords[i % n][1], coords[i % n][0]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
        
    return inside

# Test with geocoded points
print("Via Torbole (North Rome):", is_point_in_polygon(41.9514130, 12.4500717, polygon_str))
print("Pantano Borghese:", is_point_in_polygon(41.8642826, 12.7051037, polygon_str))
print("Piazza Navona (Inside):", is_point_in_polygon(41.8991, 12.4731, polygon_str))
