from geopy.distance import geodesic
import json

def spocitej_vzalenost(point1, point2):
    distance = (geodesic(point1, point2).kilometers)
    print(distance)
    return distance

export = json.load(open("export.geojson"))

olomouc_supermarkets = []

for feature in export.get("features", []):
    props = feature.get("properties", {})
    city = props.get("addr:city", "")
    branch = props.get("branch", "")
    shop_type = props.get("shop", "")
    

    if shop_type == "supermarket" and ("Olomouc" in city or "Olomouc" in branch):
        supermarket_dict = {
            "name": props.get("name", props.get("brand", "Unknown")),
            "street": props.get("addr:street", "Unknown"),
            "city": city if city else "Olomouc",
            "geometry": feature.get("geometry")
        }
        olomouc_supermarkets.append(supermarket_dict)

print(olomouc_supermarkets)