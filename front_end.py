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


def draw_circle(m: folium.Map, radius: int, coords):
    folium.Circle(
        location=coords,
        radius=radius,
        color="blue",
        weight=1,
        fill=True,
        fill_opacity=0.1,
        popup=f"{radius} meters",
        tooltip="I am in meters",
    ).add_to(m)
    icon = folium.Icon(color="#0000FF", icon="house", prefix="fa")
    folium.Marker(coords, icon=icon).add_to(m)


selected = st_searchbox(
    suggest,
    placeholder="Enter a location",
    key="address_search",
)

radius = 500
default_center = [49.5955, 17.2518]
default_zoom = 12.5

if not selected:
    m = folium.Map(location=default_center, zoom_start=default_zoom)
    st_folium(m, width=725, key="map", returned_objects=[])
else:
    coords = addresses.get(selected) or search_location(selected)
    if not coords:
        st.error("Could not find that location.")
    else:
        m = folium.Map(location=coords, zoom_start=default_zoom)
        draw_circle(m, radius, coords)
        st_folium(m, width=725, key="map", returned_objects=[])
        for typ in instituce.TYPY:
            seznam = instituce.najdi_instituce(coords, typ, radius / 1000)
            st.write(f"### {typ} ({len(seznam)})")
            for i in seznam:
                st.write(f"- {i['nazev']} ({i['vzdalenost_m']} m)")