import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

def search_location(location_name : str):
    loc = Nominatim(user_agent="Geopy Library").geocode(location_name)
    return [loc.latitude, loc.longitude] if loc else None

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

m = folium.Map(location=search_location("Olomouc"), zoom_start=12)

radius = 1000
coords = search_location("Jazz Tibet Club, Olomouc")
draw_circle(m, radius, coords)
folium.Marker(coords).add_to(m)
st_data = st_folium(m, width=725)