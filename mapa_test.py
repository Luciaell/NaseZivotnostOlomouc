import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

def search_location(location_name : str):
        try:
            loc = Nominatim(user_agent="Geopy Library").geocode(location_name)
            return [loc.latitude, loc.longitude] if loc else None
        except Exception:
            return None

def draw_circle(map : folium.Map, radius : int, coords : tuple):
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

if coords is None:
    st.error("Could not find that location.")
else:
    m = folium.Map(location=coords, zoom_start=14)
    draw_circle(m, radius, coords)
    st_folium(m, width=725, key="map", returned_objects=[])