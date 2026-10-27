def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A,B,C,D):
    # return true if AB and CD intersect (strictly or endpoint)
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

poly_unificato = [
    [41.911763, 12.477207],
    [41.910741, 12.472959],
    [41.905599, 12.475147],
    [41.901510, 12.469482],
    [41.900999, 12.464333],
    [41.899338, 12.463818],
    [41.896763, 12.464525],
    [41.895420, 12.461398],
    [41.893106, 12.462082],
    [41.893483, 12.464240],
    [41.890626, 12.466556],
    [41.889258, 12.465221],
    [41.885729, 12.471676],
    [41.886028, 12.477003],
    [41.888791, 12.479360],
    [41.890777, 12.479010],
    [41.892758, 12.481842],
    [41.895377, 12.482786],
    [41.896655, 12.486477],
    [41.898188, 12.490211],
    [41.900297, 12.492571],
    [41.902149, 12.490854],
    [41.903108, 12.488923],
    [41.904130, 12.487507],
    [41.905982, 12.483130],
    [41.911763, 12.477207]
]

n = len(poly_unificato) - 1
intersections = []
for i in range(n):
    p1 = poly_unificato[i]
    p2 = poly_unificato[i+1]
    for j in range(i+2, n):
        if i == 0 and j == n-1:
            continue
        p3 = poly_unificato[j]
        p4 = poly_unificato[j+1]
        if intersect(p1, p2, p3, p4):
            intersections.append((i, j, p1, p2, p3, p4))

print("Intersezioni trovate:", len(intersections))
for item in intersections:
    print(f"Segmento {item[0]} e {item[1]} si intersecano!")
