import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.point import Point
import vypocet_test

geolocator = Nominatim(user_agent="Geopy Library")

# returns city boundary box (4 point extremes)
def get_city_bbox(city: str):
     loc = geolocator.geocode(city, timeout=10)
     if not loc:
          return None
     south, north, west, east = map(float, loc.raw["boundingbox"])
     return (south, west, north, east)

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
        addressdetails=True
        )
    return [loc.latitude, loc.longitude] if loc else None

def draw_circle(map: folium.Map, radius: int, coords: tuple):
    folium.Circle(
    location=coords,
    radius=radius,
    color="blue",
    weight=3,
    fill_opacity=0.6,
    opacity=1,
    fill_color="blue",
    fill=False,  # gets overridden by fill_color
    popup="{} meters".format(radius),
    tooltip="I am in meters",
).add_to(map)
    folium.Marker(coords).add_to(m)

m = folium.Map(location=[49.6363900, 17.3643839], zoom_start=12)
with st.form("search_form"):
    query = st.text_input(
        "Search",
        placeholder="Enter a location",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Search")

radius = 1000
coords = search_location(query)

if not coords:
    st.error("Could not find that location.")
else:
    m = folium.Map(location=coords, zoom_start=14)
    draw_circle(m, radius, coords)
    st_folium(m, width=725, key="map", returned_objects=[])