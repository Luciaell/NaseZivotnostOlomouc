"""Find institutions within a given distance of a point in Olomouc.

Usage:
    from back_end import find_institutions, TYPES
    pharmacies = find_institutions((49.5938, 17.2509), "pharmacies")  # point = (lat, lon)
    # -> [{"name": ..., "distance_m": ..., "lat": ..., "lon": ..., "osm_id": ...}, ...]
"""

import json
from functools import lru_cache
from pathlib import Path

from geopy.distance import geodesic

DATASETS = Path(__file__).parent / "datasets"
OLOMOUC_BOUNDARY = DATASETS / "olomouc_boundary.geojson"

# category key -> (file name, fallback name when the feature has none)
# Details of each dataset: "md files of datasets/<file name>.md"
CATEGORIES = {
    "bus_stops": ("bus_stop.geojson", "Zastávka (bez názvu)"),
    "tram_stops": ("tramvaj_zastavka.geojson", "Zastávka tramvaje (bez názvu)"),
    "train_stations": ("vlak_zastavka.geojson", "Nádraží (bez názvu)"),
    "kindergartens": ("kindergarten.geojson", "MŠ (bez názvu)"),
    "schools": ("zakladni_skola.geojson", "ZŠ (bez názvu)"),
    "libraries": ("knihovna.geojson", "Knihovna (bez názvu)"),
    "pharmacies": ("pharmacy.geojson", "Lékárna (bez názvu)"),
    "supermarkets": ("supermarket.geojson", "Supermarket (bez názvu)"),
    "restaurants": ("restaurace_hospody_bary_cluby.geojson", "Restaurace (bez názvu)"),  # restaurants only, no pubs/bars/clubs yet
    "theatres": ("divadlo.geojson", "Divadlo (bez názvu)"),
    "cinemas": ("kino.geojson", "Kino (bez názvu)"),
    "gyms": ("gym.geojson", "Posilovna (bez názvu)"),
    "sports_halls": ("sportovni_hala.geojson", "Sportovní hala (bez názvu)"),  # only 1 entry, needs re-export
    "places_of_worship": ("nabozenska_budova.geojson", "Kostel (bez názvu)"),  # only small chapels, needs re-export
}

# Types whose data has several points per stop (platforms, stop positions);
# results keep only the nearest point per name.
MERGE_BY_NAME = {"bus_stops", "tram_stops", "train_stations"}


# Property keys holding a feature's name: OSM uses "name", the regional
# open data uses "NAZEV" (libraries) or "ORG_NAZEV" (schools).
NAME_KEYS = ("name", "NAZEV", "ORG_NAZEV")

# Heat-perception survey (2020). Details: "md files of datasets/pocitova-teplotni-mapa-olomouce-2.md"
HEAT_MAP = DATASETS / "pocitova-teplotni-mapa-olomouce-2.geojson"
# Heatmap weight per felt-temperature answer (desc_teplota): hot places count most.
HEAT_WEIGHTS = {
    "velká zima": 0.0, "zima": 0.0, "chladno": 0.05, "mírně chladno": 0.1, "neutrální": 0.2,
    "mírně teplo": 0.4, "teplo": 0.6, "horko": 0.8, "velmi horko": 1.0,
}
# No rating given: fall back on the question answered ("a" = feels unpleasant on hot days,
# "b" = feels pleasant).
HEAT_FALLBACK = {"a": 0.8, "b": 0.2}
MAX_HEAT_AREA_M2 = 2_000_000   # larger polygons are drawing mistakes (one covers half a continent)
M_PER_DEG_LAT, M_PER_DEG_LON = 111_320, 72_100   # at Olomouc's latitude (~49.6°)


# --- geometry helpers (lon/lat treated as planar; fine at city scale) ---

def _ring_centroid(ring):
    """Area centroid of a polygon ring [[lon, lat], ...]. Returns (lon, lat)."""
    area = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        k = x0 * y1 - x1 * y0
        area += k
        cx += (x0 + x1) * k
        cy += (y0 + y1) * k
    if abs(area) < 1e-15:  # degenerate ring -> mean of vertices
        return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
    area *= 0.5
    return (cx / (6 * area), cy / (6 * area))


def _geometry_center(geometry):
    """Point for a GeoJSON geometry: the point itself, or the outer-ring centroid."""
    kind, coords = geometry["type"], geometry["coordinates"]
    if kind == "Point":
        return tuple(coords[:2])
    if kind == "Polygon":
        return _ring_centroid(coords[0])
    if kind == "MultiPolygon":  # use the largest part's outer ring
        return _ring_centroid(max((p[0] for p in coords), key=len))
    raise ValueError(f"Unsupported geometry type: {kind}")


def _ring_area_m2(ring):
    """Approximate area of a ring [[lon, lat], ...] in square metres (shoelace formula)."""
    doubled = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:]))
    return abs(doubled) / 2 * M_PER_DEG_LAT * M_PER_DEG_LON


def _point_in_ring(lon, lat, ring):
    """Ray-casting point-in-polygon test for one ring."""
    inside = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        if (y0 > lat) != (y1 > lat):
            if lon < x0 + (lat - y0) * (x1 - x0) / (y1 - y0):
                inside = not inside
    return inside


def _point_in_polygon(lon, lat, polygon):
    """polygon = [outer_ring, hole1, ...]"""
    if not _point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(_point_in_ring(lon, lat, hole) for hole in polygon[1:])


# --- data loading (cached so Streamlit reruns don't re-read files) ---

@lru_cache(maxsize=1)
def _boundary():
    """List of polygons making up the Olomouc city boundary."""
    data = json.loads(OLOMOUC_BOUNDARY.read_text(encoding="utf-8"))
    polygons = []
    for f in data["features"]:
        g = f["geometry"]
        polygons.extend([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])
    return polygons


def is_in_olomouc(lat, lon):
    """True if the point lies inside the Olomouc city boundary."""
    return any(_point_in_polygon(lon, lat, p) for p in _boundary())


@lru_cache(maxsize=None)
def _load_category(key):
    """Load one category, keeping only features whose point lies in Olomouc."""
    file_name, default_name = CATEGORIES[key]
    data = json.loads((DATASETS / file_name).read_text(encoding="utf-8"))
    institutions, seen = [], set()
    for f in data["features"]:
        lon, lat = _geometry_center(f["geometry"])
        if not is_in_olomouc(lat, lon):
            continue
        p = f.get("properties", {})
        name = next((p[k] for k in NAME_KEYS if p.get(k)), None)
        # regional data lists a school once per school type at the same point
        if name and (name, lat, lon) in seen:
            continue
        seen.add((name, lat, lon))
        institutions.append({
            "name": name or p.get("brand") or default_name,
            "has_name": bool(name),
            "lat": lat,
            "lon": lon,
            "osm_id": f.get("id") or p.get("@id"),
        })
    return tuple(institutions)


@lru_cache(maxsize=1)
def heat_points():
    """Heat-perception survey answers as heatmap points: tuple of (lat, lon, weight).

    Polygons are reduced to their centroid; oversized polygons and answers outside
    Olomouc are dropped. Weight 0..1 comes from HEAT_WEIGHTS (hot = 1).
    """
    data = json.loads(HEAT_MAP.read_text(encoding="utf-8"))
    points = []
    for f in data["features"]:
        g, p = f["geometry"], f["properties"]
        if g["type"] == "Polygon" and _ring_area_m2(g["coordinates"][0]) > MAX_HEAT_AREA_M2:
            continue
        lon, lat = _geometry_center(g)
        if not is_in_olomouc(lat, lon):
            continue
        weight = HEAT_WEIGHTS.get(p.get("desc_teplota"), HEAT_FALLBACK.get(p.get("typ_ident")))
        if weight:   # skip None and 0 (cold answers add no heat)
            points.append((lat, lon, weight))
    return tuple(points)


# --- public API ---

TYPES = tuple(CATEGORIES)  # all valid institution types, e.g. for frontend checkboxes


def find_institutions(point, kind, radius_km=1.0):
    """Return institutions of one type within `radius_km` of `point`.

    point: (lat, lon) tuple
    kind: one of TYPES (e.g. "bus_stops", "pharmacies", "libraries")

    Result: [ {name, distance_m, lat, lon, osm_id}, ... ] sorted by distance.
    For types in MERGE_BY_NAME, points sharing a name are merged into one
    stop (the nearest point is kept).

    Raises ValueError if the type is unknown or the point is outside Olomouc.
    """
    if kind not in CATEGORIES:
        raise ValueError(f"Unknown institution type: {kind!r}. Valid types: {', '.join(TYPES)}")
    lat, lon = point
    if not is_in_olomouc(lat, lon):
        raise ValueError(f"Point ({lat}, {lon}) is not in Olomouc.")

    found = []
    for inst in _load_category(kind):
        distance_m = geodesic((lat, lon), (inst["lat"], inst["lon"])).meters
        if distance_m <= radius_km * 1000:
            found.append({
                "name": inst["name"],
                "distance_m": round(distance_m),
                "lat": inst["lat"],
                "lon": inst["lon"],
                "osm_id": inst["osm_id"],
                "_has_name": inst["has_name"],
            })
    found.sort(key=lambda x: x["distance_m"])

    if kind in MERGE_BY_NAME:
        found = _merge_by_name(found)

    for n in found:
        n.pop("_has_name")
    return found


find = find_institutions  # short alias


def _merge_by_name(stops):
    """Keep only the nearest point per stop name (input sorted by distance)."""
    seen, merged = set(), []
    for s in stops:
        if s["_has_name"]:
            if s["name"] in seen:
                continue
            seen.add(s["name"])
        merged.append(s)
    return merged


if __name__ == "__main__":
    # quick manual test: Horní náměstí
    for category in TYPES:
        results = find_institutions((49.5938, 17.2509), category)
        print(f"\n{category} ({len(results)}):")
        for i in results:
            print(f"  {i['distance_m']:>5} m  {i['name']}")
