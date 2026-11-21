import os
import unicodedata

import folium
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.point import Point
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox

import instituce

geolocator = Nominatim(user_agent="Geopy Library")

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "nase-zivotnost-ol/1.0"}
MIN_CHARS = 2      # suggestions appear after this many characters
MAX_RESULTS = 10


def normalize(s: str) -> str:
    # Lowercase and strip diacritics, so 'kat' matches 'Kateřinská'.
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


@st.cache_data(show_spinner=False)
def get_city_bbox(city: str):
    loc = geolocator.geocode(city, timeout=10)
    if not loc:
        return None
    south, north, west, east = map(float, loc.raw["boundingbox"])
    return (south, west, north, east)


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading addresses...")
def fetch_addresses() -> dict[str, list[float]]:
    # Returns {"Kateřinská 12": [lat, lon], ...} for all address points in the box.
    south, west, north, east = get_city_bbox("Olomouc")
    query = f"""
    [out:json][timeout:40];
    nwr["addr:housenumber"]["addr:street"]({south},{west},{north},{east});
    out tags center qt;
    """
    last_error = None
    for url in OVERPASS_URLS:
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=60)
            r.raise_for_status()
            data = r.json()
            if "elements" not in data:
                raise RuntimeError(data.get("remark", "No elements in response"))
            addresses = {}
            for el in data["elements"]:
                tags = el["tags"]
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if lat is None:
                    continue
                # Czech style: conscription number / orientation number (e.g. 123/4)
                cp, co = tags.get("addr:conscriptionnumber"), tags.get("addr:streetnumber")
                number = f"{cp}/{co}" if cp and co else tags["addr:housenumber"]
                addresses[f"{tags['addr:street']} {number}"] = [lat, lon]
            return addresses
        except Exception as e:
            last_error = e
    raise RuntimeError(f"All Overpass servers failed: {last_error}")  # not cached


def get_addresses() -> dict[str, list[float]]:
    try:
        return fetch_addresses()
    except Exception as e:
        st.warning(f"Address list unavailable ({e}). Free-text search still works.")
        return {}


@st.cache_data(show_spinner=False)
def search_location(query: str):
    bbox = get_city_bbox("Olomouc")
    if bbox is None:
        return None
    south, west, north, east = bbox
    loc = geolocator.geocode(
        query,
        timeout=10,
        viewbox=[Point(south, west), Point(north, east)],
        bounded=True,
        addressdetails=True,
    )
    return [loc.latitude, loc.longitude] if loc else None


addresses = get_addresses()
labels = sorted(addresses)
normalized = [(normalize(label), label) for label in labels]


def suggest(searchterm: str) -> list[str]:
    # Called by the searchbox on every keystroke.
    if len(searchterm) < MIN_CHARS:
        return []
    term = normalize(searchterm)
    starts = [lab for n, lab in normalized if n.startswith(term)]
    contains = [lab for n, lab in normalized if term in n and not n.startswith(term)]
    results = (starts + contains)[:MAX_RESULTS]
    # let the user pick their exact text even if it's not in the list
    if searchterm not in results:
        results.append(searchterm)
    return results

def circle_color(results: dict[str, list]) -> str:
    missing = sum(1 for seznam in results.values() if not seznam)
    if missing == 0:
        return "green"
    if missing == 1:
        return "#ff6600"
    return "red"

def dist_color(dist: float) -> str:
    if dist < 200:
        return "green"
    if dist < 350:
        return "orange"
    return "red"

def draw_circle(m: folium.Map, radius: int, coords, color: str = "blue"):
    folium.Circle(
        location=coords,
        radius=radius,
        color=color,
        weight=1,
        fill=True,
        fill_color=color,
        fill_opacity=0.1
    ).add_to(m)
    icon = folium.Icon(color=color, icon="house", prefix="fa")
    folium.Marker(coords, icon=icon).add_to(m)


selected = st_searchbox(
    suggest,
    placeholder="Enter a location",
    key="address_search",
)

radius = 500 # metres
default_center = [49.5955, 17.2518]
default_zoom = 12.5

MARKER_STYLES = {
    "zastavky":     {"color": "blue",      "icon": "bus"},
    "skolky":       {"color": "orange",    "icon": "child"},
    "lekarny":      {"color": "green",     "icon": "pills"},
    "skoly":        {"color": "red",       "icon": "school"},
    "supermarkety": {"color": "purple",    "icon": "cart-shopping"},
}
DEFAULT_STYLE = {"color": "gray", "icon": "location-dot"}

def add_marker(m: folium.Map, typ: str, item: dict):
    style = MARKER_STYLES.get(typ, DEFAULT_STYLE)
    folium.Marker(
        location=[item["lat"], item["lon"]],
        tooltip=f"{item['nazev']} ({item['vzdalenost_m']} m)",
        icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
    ).add_to(m)

CARTO_ATTR = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>'
)

def get_carto_key() -> str | None:
    try:
        return st.secrets["CARTO_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("CARTO_API_KEY")

def make_map(coords, zoom, style="voyager"):
    # style: "voyager", "positron" (light_all) or "dark_matter" (dark_all)
    key = get_carto_key()
    if not key:
        return folium.Map(location=coords, zoom_start=zoom)   # plain OSM fallback

    path = {"voyager": "voyager", "positron": "light_all", "dark_matter": "dark_all"}[style]
    return folium.Map(
        location=coords,
        zoom_start=zoom,
        tiles=f"https://basemaps.cartocdn.com/rastertiles/{path}/{{z}}/{{x}}/{{y}}{{r}}.png?key={key}",
        attr=CARTO_ATTR,
    )

if not selected:
    m = make_map(default_center, default_zoom)
    st_folium(m, width=725, key="map", returned_objects=[])
else:
    coords = addresses.get(selected) or search_location(selected)
    if not coords:
        st.error("Could not find that location.")
    else:
        m = make_map(coords, 14)
        results = {}
        nearest = {}
        for typ in instituce.TYPY:
            seznam = instituce.najdi_instituce(coords, typ, radius / 1000)
            results[typ] = seznam
            if seznam:
                nearest[typ] = min(seznam, key=lambda i: i["vzdalenost_m"])
            for i in seznam:
                add_marker(m, typ, i)
            if typ in nearest:
                st.write(f":{dist_color(nearest[typ]['vzdalenost_m'])}[Nejbližší {typ}: {nearest[typ]['nazev']} ({nearest[typ]['vzdalenost_m']} m)]")
            else:
                st.write(f":{dist_color(0)}Nejbližší {typ}: žádný v okruhu {radius} m")

    draw_circle(m, radius, coords, color=circle_color(results))
    st_folium(m, width=725, key="map", returned_objects=[])