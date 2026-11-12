import streamlit as st

#USER INTERFACE - Luci
def slider_dulezitost(label):
    return st.slider(
        label,
        min_value=0.0,                   # Minimum value
        max_value=1.0,                 # Maximum value
        value=0.5,                      # Default value
        step=0.01,                        # Step size
    format="percent"               # Format of the values
)

#různé slidery důležitosti pro různé kategorie
slider_supermarkety=slider_dulezitost(label="supermarkety")
slider_skoly=slider_dulezitost(label="školy")
slider_zdravotnictvi=slider_dulezitost(label="zdravotnictví")

st.metric(
    label="index žití",
    value=2.0,
    border=True
)