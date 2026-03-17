import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Oblicza odległość między dwoma punktami na Ziemi (w kilometrach)
    
    :param lat1: szerokość geograficzna punktu 1
    :param lon1: długość geograficzna punktu 1
    :param lat2: szerokość geograficzna punktu 2
    :param lon2: długość geograficzna punktu 2
    :return: odległość w kilometrach
    """

    # Promień Ziemi w km
    R = 6371.0

    # Zamiana stopni na radiany
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Różnice współrzędnych
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Wzór Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance