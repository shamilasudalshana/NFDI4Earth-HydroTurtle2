import streamlit as st
import pandas as pd

def delimiter_selection(file_name):

    delimiter = st.selectbox(
        f"Select CSV delimiter for {file_name.name}",
        options=[
            "; (Semicolon)",
            ", (Comma)",
            "Space",
            "\t (Tab)",
        ],
    )

    # Convert user selection to actual delimiter value
    if delimiter == "; (Semicolon)":
        delimiter = ";"
    elif delimiter == ", (Comma)":
        delimiter = ","
    elif delimiter == "Space":
        delimiter = " "
    else:  # "\t (Tab)"
        delimiter = "\t"

    return delimiter