"""Find institutions within a given distance of a point in Olomouc.

Usage:
    from instituce import najdi_instituce, TYPY
    lekarny = najdi_instituce((49.5938, 17.2509), "lekarny")  # bod = (lat, lon)
    # -> [{"nazev": ..., "vzdalenost_m": ..., "lat": ..., "lon": ..., "osm_id": ...}, ...]
"""

import json
from functools import lru_cache
from pathlib import Path

from geopy.distance import geodesic

DATASETS = Path(__file__).parent / "datasets"
HRANICE_OLOMOUCE = DATASETS / "olomouc_boundary.geojson"

# category key -> (file name, fallback name when OSM has none)
KATEGORIE = {
    "zastavky": ("bus_stop.geojson", "Zastávka (bez názvu)"),
    "skolky": ("kindergarten.geojson", "MŠ (bez názvu)"),
    "lekarny": ("pharmacy.geojson", "Lékárna (bez názvu)"),
    "skoly": ("primary_school.geojson", "ZŠ (bez názvu)"),
    "supermarkety": ("supermarket.geojson", "Supermarket (bez názvu)"),
}


# --- geometry helpers (lon/lat treated as planar; fine at city scale) ---

def _centroid_kruhu(kruh):
    """Area centroid of a polygon ring [[lon, lat], ...]. Returns (lon, lat)."""
    plocha = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(kruh, kruh[1:]):
        k = x0 * y1 - x1 * y0
        plocha += k
        cx += (x0 + x1) * k
        cy += (y0 + y1) * k
    if abs(plocha) < 1e-15:  # degenerate ring -> mean of vertices
        return (sum(p[0] for p in kruh) / len(kruh), sum(p[1] for p in kruh) / len(kruh))
    plocha *= 0.5
    return (cx / (6 * plocha), cy / (6 * plocha))


def _stred_geometrie(geometrie):
    """Point for a GeoJSON geometry: the point itself, or the outer-ring centroid."""
    typ, sour = geometrie["type"], geometrie["coordinates"]
    if typ == "Point":
        return tuple(sour[:2])
    if typ == "Polygon":
        return _centroid_kruhu(sour[0])
    if typ == "MultiPolygon":  # use the largest part's outer ring
        return _centroid_kruhu(max((p[0] for p in sour), key=len))
    raise ValueError(f"Nepodporovaný typ geometrie: {typ}")


def _bod_v_kruhu(lon, lat, kruh):
    """Ray-casting point-in-polygon test for one ring."""
    uvnitr = False
    for (x0, y0), (x1, y1) in zip(kruh, kruh[1:]):
        if (y0 > lat) != (y1 > lat):
            if lon < x0 + (lat - y0) * (x1 - x0) / (y1 - y0):
                uvnitr = not uvnitr
    return uvnitr


def _bod_v_polygonu(lon, lat, polygon):
    """polygon = [outer_ring, hole1, ...]"""
    if not _bod_v_kruhu(lon, lat, polygon[0]):
        return False
    return not any(_bod_v_kruhu(lon, lat, dira) for dira in polygon[1:])


# --- data loading (cached so Streamlit reruns don't re-read files) ---

@lru_cache(maxsize=1)
def _hranice():
    """List of polygons making up the Olomouc city boundary."""
    data = json.loads(HRANICE_OLOMOUCE.read_text(encoding="utf-8"))
    polygony = []
    for f in data["features"]:
        g = f["geometry"]
        polygony.extend([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])
    return polygony


def je_v_olomouci(lat, lon):
    """True if the point lies inside the Olomouc city boundary."""
    return any(_bod_v_polygonu(lon, lat, p) for p in _hranice())


@lru_cache(maxsize=None)
def _nacti_kategorii(klic):
    """Load one category, keeping only features whose point lies in Olomouc."""
    soubor, vychozi_nazev = KATEGORIE[klic]
    data = json.loads((DATASETS / soubor).read_text(encoding="utf-8"))
    instituce = []
    for f in data["features"]:
        lon, lat = _stred_geometrie(f["geometry"])
        if not je_v_olomouci(lat, lon):
            continue
        p = f.get("properties", {})
        instituce.append({
            "nazev": p.get("name") or p.get("brand") or vychozi_nazev,
            "ma_nazev": bool(p.get("name")),
            "lat": lat,
            "lon": lon,
            "osm_id": f.get("id") or p.get("@id"),
        })
    return tuple(instituce)


# --- public API ---

TYPY = tuple(KATEGORIE)  # all valid institution types, e.g. for frontend checkboxes


def najdi_instituce(bod, typ, radius_km=1.0):
    """Return institutions of one type within `radius_km` of `bod`.

    bod: (lat, lon) tuple
    typ: one of TYPY ("zastavky", "skolky", "lekarny", "skoly", "supermarkety")

    Result: [ {nazev, vzdalenost_m, lat, lon, osm_id}, ... ] sorted by distance.
    Bus stop platforms sharing a name are merged into one stop (the nearest
    platform is kept).

    Raises ValueError if the type is unknown or the point is outside Olomouc.
    """
    if typ not in KATEGORIE:
        raise ValueError(f"Neznámý typ instituce: {typ!r}. Platné typy: {', '.join(TYPY)}")
    lat, lon = bod
    if not je_v_olomouci(lat, lon):
        raise ValueError(f"Bod ({lat}, {lon}) neleží v Olomouci.")

    nalezene = []
    for inst in _nacti_kategorii(typ):
        vzdalenost_m = geodesic((lat, lon), (inst["lat"], inst["lon"])).meters
        if vzdalenost_m <= radius_km * 1000:
            nalezene.append({
                "nazev": inst["nazev"],
                "vzdalenost_m": round(vzdalenost_m),
                "lat": inst["lat"],
                "lon": inst["lon"],
                "osm_id": inst["osm_id"],
                "_ma_nazev": inst["ma_nazev"],
            })
    nalezene.sort(key=lambda x: x["vzdalenost_m"])

    if typ == "zastavky":
        nalezene = _sluc_nastupiste(nalezene)

    for n in nalezene:
        n.pop("_ma_nazev")
    return nalezene


najdi = najdi_instituce  # short alias


def _sluc_nastupiste(zastavky):
    """Keep only the nearest platform per stop name (input sorted by distance)."""
    videne, sloucene = set(), []
    for z in zastavky:
        if z["_ma_nazev"]:
            if z["nazev"] in videne:
                continue
            videne.add(z["nazev"])
        sloucene.append(z)
    return sloucene


if __name__ == "__main__":
    # quick manual test: Horní náměstí
    for kategorie in TYPY:
        seznam = najdi_instituce((49.5938, 17.2509), kategorie)
        print(f"\n{kategorie} ({len(seznam)}):")
        for i in seznam:
            print(f"  {i['vzdalenost_m']:>5} m  {i['nazev']}")


num = 0

for item in najdi_instituce((49.5958, 17.2509), "lekarny", 1.0):
    print(f"  {item['nazev']}")
    num += 1

print (num)