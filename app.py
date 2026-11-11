import streamlit as st

st.slider(
    label="nastavení důležitosti",  # Label as a string parameter
    min_value=0.0,                   # Minimum value
    max_value=1.0,                 # Maximum value
    value=0.5,                      # Default value
    step=0.01,                        # Step size
    format="percent"               # Format of the values
)
