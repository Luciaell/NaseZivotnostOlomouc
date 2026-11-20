import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.point import Point

geolocator = Nominatim(user_agent="Geopy Library")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:60];
area["name"="Olomouc"]["boundary"="administrative"]["admin_level"="8"]->.city;
way(area.city)["highway"]["name"];
out tags;
"""


# list of street names in Olomouc, fetched once a day
@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading streets...")
def get_streets() -> list[str]:
    try:
        r = requests.post(OVERPASS_URL, data={"data": OVERPASS_QUERY}, timeout=90)
        r.raise_for_status()
        return sorted({el["tags"]["name"] for el in r.json()["elements"]})
    except Exception:
        return []


# returns city bounding box (4 point extremes)
@st.cache_data(show_spinner=False)
def get_city_bbox(city: str):
    loc = geolocator.geocode(city, timeout=10)
    if not loc:
        return None
    south, north, west, east = map(float, loc.raw["boundingbox"])
    return (south, west, north, east)


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


def draw_circle(m: folium.Map, radius: int, coords):
    folium.Circle(
        location=coords,
        radius=radius,
        color="blue",
        weight=3,
        fill=False,
        opacity=1,
        popup=f"{radius} meters",
        tooltip="I am in meters",
    ).add_to(m)
    folium.Marker(coords).add_to(m)


streets = get_streets()
if not streets:
    st.warning("Street list unavailable, you can still type an address manually.")

with st.form("search_form"):
    query = st.selectbox(
        "Search",
        options=streets,
        index=None,                      # start empty
        placeholder="Enter a location",
        accept_new_options=True,         # typed text doesn't have to be in the list
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Search")

radius = 1000
default_center = [49.6363900, 17.3643839]

if not query:
    # nothing searched yet: show the default map
    m = folium.Map(location=default_center, zoom_start=12)
    st_folium(m, width=725, key="map", returned_objects=[])
else:
    coords = search_location(query)
    if not coords:
        st.error("Could not find that location.")
    else:
        m = folium.Map(location=coords, zoom_start=14)
        draw_circle(m, radius, coords)
        st_folium(m, width=725, key="map", returned_objects=[])