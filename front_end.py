import os
import unicodedata

import folium
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.point import Point
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox

import back_end

st.set_page_config(layout="wide")  # must run before any other st.* call

USER_AGENT = "nase-zivotnost-ol/1.0"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
MIN_CHARS = 2      # suggestions appear after this many characters
MAX_RESULTS = 10

RADIUS_M = 500
DEFAULT_CENTER = [49.5955, 17.2518]
DEFAULT_ZOOM = 12.5
SELECTED_ZOOM = 15

# One entry per type in back_end.TYPES: Czech label, map marker style (Font Awesome
# `icon`) and the summary icon (`symbol`, a Google Material Symbol name).
KINDS = {
    "bus_stops":         {"label": "zastávka",          "color": "blue",       "icon": "bus",           "symbol": "directions_bus"},
    "tram_stops":        {"label": "zastávka tramvaje", "color": "darkblue",   "icon": "train-tram",    "symbol": "tram"},
    "train_stations":    {"label": "vlakové nádraží",   "color": "cadetblue",  "icon": "train",         "symbol": "train"},
    "kindergartens":     {"label": "mateřská škola",    "color": "orange",     "icon": "child",         "symbol": "child_care"},
    "schools":           {"label": "základní škola",    "color": "red",        "icon": "school",        "symbol": "school"},
    "libraries":         {"label": "knihovna",          "color": "darkred",    "icon": "book",          "symbol": "local_library"},
    "pharmacies":        {"label": "lékárna",           "color": "green",      "icon": "pills",         "symbol": "local_pharmacy"},
    "supermarkets":      {"label": "supermarket",       "color": "purple",     "icon": "cart-shopping", "symbol": "shopping_cart"},
    "restaurants":       {"label": "restaurace",        "color": "beige",      "icon": "utensils",      "symbol": "restaurant"},
    "theatres":          {"label": "divadlo",           "color": "darkpurple", "icon": "masks-theater", "symbol": "theater_comedy"},
    "cinemas":           {"label": "kino",              "color": "pink",       "icon": "film",          "symbol": "movie"},
    "gyms":              {"label": "posilovna",         "color": "darkgreen",  "icon": "dumbbell",      "symbol": "fitness_center"},
    "sports_halls":      {"label": "sportovní hala",    "color": "lightgreen", "icon": "volleyball",    "symbol": "sports_volleyball"},
    "places_of_worship": {"label": "kostel",            "color": "black",      "icon": "church",        "symbol": "church"},
}
DEFAULT_KIND = {"color": "gray", "icon": "location-dot", "symbol": "location_on"}

CARTO_STYLES = {"voyager": "voyager", "positron": "light_all", "dark_matter": "dark_all"}
CARTO_ATTR = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>'
)

geolocator = Nominatim(user_agent=USER_AGENT)


# --- address search ---

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
            r = requests.post(url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=60)
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
normalized = [(normalize(label), label) for label in sorted(addresses)]


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


# --- map ---

def get_carto_key() -> str | None:
    try:
        return st.secrets["CARTO_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("CARTO_API_KEY")


def make_map(coords, zoom, style="voyager") -> folium.Map:
    key = get_carto_key()
    if not key:
        return folium.Map(location=coords, zoom_start=zoom)   # plain OSM fallback
    return folium.Map(
        location=coords,
        zoom_start=zoom,
        tiles=f"https://basemaps.cartocdn.com/rastertiles/{CARTO_STYLES[style]}/{{z}}/{{x}}/{{y}}{{r}}.png?key={key}",
        attr=CARTO_ATTR,
    )


def circle_color(results: dict[str, list]) -> str:
    missing = sum(1 for found in results.values() if not found)
    if missing == 0:
        return "green"
    if missing == 1:
        return "#ff6600"
    return "red"


def dist_color(dist: float) -> str:
    if dist < 300:
        return "green"
    if dist < 500:
        return "orange"
    return "red"


def draw_selected_location(m: folium.Map, coords, color: str):
    folium.Circle(
        location=coords,
        radius=RADIUS_M,
        color=color,
        weight=1,
        fill=True,
        fill_color=color,
        fill_opacity=0.1,
    ).add_to(m)
    icon = folium.Icon(color=color, icon="house", prefix="fa")
    folium.Marker(coords, icon=icon, tooltip="Vybraná lokace").add_to(m)


def add_marker(m: folium.Map, kind: str, item: dict):
    style = KINDS.get(kind, DEFAULT_KIND)
    folium.Marker(
        location=[item["lat"], item["lon"]],
        tooltip=f"{item['name']} ({item['distance_m']} m)",
        icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
    ).add_to(m)


def show_metric(kind: str, found: list[dict]):
    style = KINDS.get(kind, DEFAULT_KIND)
    label = style.get("label", kind).capitalize()
    with st.container(border=True):
        if not found:
            st.metric(f":red[:material/{style['symbol']}: {label}]", f"> {RADIUS_M} m")
            st.caption("Žádné v okolí")
            return
        nearest = found[0]  # back_end returns results sorted by distance
        color = dist_color(nearest["distance_m"])
        st.metric(f":{color}[:material/{style['symbol']}: {label}]", f"{nearest['distance_m']} m")
        st.caption(nearest["name"])


def show_results(coords):
    m = make_map(coords, SELECTED_ZOOM)
    results = {kind: back_end.find_institutions(coords, kind, RADIUS_M / 1000)
               for kind in back_end.TYPES}
    for kind, found in results.items():
        for item in found:
            add_marker(m, kind, item)
    draw_selected_location(m, coords, circle_color(results))

    col_map, col_text = st.columns([4, 3])
    with col_map:
        st_folium(m, use_container_width=True, height=500, key="map", returned_objects=[])
    with col_text:
        grid = st.columns(2)
        for i, (kind, found) in enumerate(results.items()):
            with grid[i % 2]:
                show_metric(kind, found)


# --- page ---

selected = st_searchbox(suggest, placeholder="Enter a location", key="address_search")

if not selected:
    st_folium(make_map(DEFAULT_CENTER, DEFAULT_ZOOM), width=725, key="map", returned_objects=[])
else:
    coords = addresses.get(selected) or search_location(selected)
    if not coords:
        st.error("Could not find that location.")
    elif not back_end.is_in_olomouc(*coords):
        st.error("That location is outside Olomouc.")
    else:
        show_results(coords)
