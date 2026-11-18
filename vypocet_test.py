from geopy.distance import geodesic

lidl_lazecka = (49.6026317, 17.2515500)
lidl_velkomoravska = (49.5818919, 17.2489167)


def spocitej_vzalenost(point1, point2):
    distance = (geodesic(point1, point2).kilometers)
    print(distance)
    return distance


spocitej_vzalenost(lidl_lazecka, lidl_velkomoravska)
