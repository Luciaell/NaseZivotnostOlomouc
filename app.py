import streamlit as st

st.slider(
    label="nastavení důležitosti",  # Label as a string parameter
    min_value=0,                   # Minimum value
    max_value=100,                 # Maximum value
    value=50,                      # Default value
    step=1,                        # Step size
    format="percent"               # Format of the values
)

