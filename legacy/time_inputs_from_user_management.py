import json
import streamlit as st
import pandas as pd
from io import StringIO
import time

def time_with_each_column_user_input(time_data_json_dictionary, csv_file_path, csv_content,  file_index, delimiter):
    # Read the CSV file as dataframe
    csv_file_data_frame = pd.read_csv(StringIO(csv_content), delimiter=delimiter) # stringIO to make re readble csv file wthout changing status when read several times

    #st.write(f"Data from file {file_index + 1}: \n", csv_file_data_frame)

    # Initialize default values
    parsing_method = None
    date_col = None
    time_col = None
    date_format = None
    time_format = None

    # Choose the method for date and time parsing
    parsing_method = st.radio(
        f"Choose the method for date and time parsing (File {file_index + 1})",
        ("Separate Columns for Year/Month/Day/Hour/Minute/Second",
         "Combined Date and Time Column",
         "Separate Date and Time Columns"),
        key=f"parsing_method_{file_index}"
    )

    #st.write(f"Selected parsing method for the file {csv_file_path.name}: {parsing_method}")  # Debugging print

    if parsing_method == "Separate Date and Time Columns":
        #st.write("Separate Date and Time Columns selected")

        date_col = st.selectbox(
            f"Select the :violet[date] column (File {file_index + 1}):",
            csv_file_data_frame.columns,
            key=f"date_col_{file_index}"
        )
        # addition of "NA" option to time_col variable
        columns_with_option = list(csv_file_data_frame.columns) + ["Not Applicable"]

        time_col = st.selectbox(
            f"Select the :violet[time] column (File {file_index + 1}):",
            columns_with_option,
            key=f"time_col_{file_index}"
        )

        if time_col == "Not Applicable":
            time_col = None

        common_date_formats = [
            "%d:%m:%Y", "%d/%m/%Y", "%m/%d/%Y",
            "%m-%d-%Y", "%Y.%m.%d", "%Y-%m-%d"
        ]

        common_time_formats = [
            "%H:%M:%S", "%H/%M/%S", "%I:%M:%S %p", "%H.%M.%S"
        ]

        date_format = st.selectbox(
            f"Select the :blue[date format] (File {file_index + 1}):",
            common_date_formats,
            key=f"date_format_{file_index}"
        )
        time_format = st.selectbox(
            f"Select the :blue[time format] (File {file_index + 1}):",
            common_time_formats,
            key=f"time_format_{file_index}"
        )

        #st.write(f"{parsing_method} captured")

    elif parsing_method == "Separate Columns for Year/Month/Day/Hour/Minute/Second":
        st.markdown(
            f"***Please provide the exact column heading related time in your CSV file to generate accurate triples for file {file_index + 1}.*** "
            ":red[**If some of the columns are not available in your dataset please select 'Not applicable' option**]"
        )

        # Initialize the variables list for the time and date related from the keys of time_data_json
        time_date_dictionary_keys = ["year", "month", "day", "hour", "minute", "second", "dateOfYear"]

        # Adding "Not Available" option to the column list
        columns_with_option = list(csv_file_data_frame.columns) + ["Not Applicable"]

        # Function to handle the selectbox and dictionary update
        def process_column(variable_name):
            col_heading = st.selectbox(
                f"Provide the :violet[{variable_name}] input for column in the CSV file '{csv_file_path.name}' (File {file_index + 1}):",
                columns_with_option,
                key=f"{variable_name}_{file_index}"
            )
            if col_heading != "Not Applicable":
                time_data_json_dictionary[variable_name] = col_heading

        # Loop through each variable and process it
        for variable in time_date_dictionary_keys:
            process_column(variable)

        st.write(f"{parsing_method} captured")

        date_col, time_col, date_format, time_format = None, None, None, None

    elif parsing_method == 'Combined Date and Time Column':
        #st.write("Combined Date and Time Column selected")

        date_col = st.selectbox(
            f"Select the combined date and time column (File {file_index + 1}):",
            csv_file_data_frame.columns,
            key=f"combined_col_{file_index}"
        )
        time_col = None

        common_datetime_formats = [
            "%d:%m:%Y %H:%M:%S", "%d/%m/%Y %H/%M/%S", "%m/%d/%Y %H/%M/%S",
            "%m-%d-%Y %H:%M:%S", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"
        ]

        date_format = st.selectbox(
            f"Select the date and time format (File {file_index + 1}):",
            common_datetime_formats,
            key=f"datetime_format_{file_index}"
        )
        time_format = None  # Not needed for combined date and time column

        st.write(f"{parsing_method} captured")

    else:
        st.markdown(":red[this is still in progress]")
        date_col, time_col, date_format, time_format = None, None, None, None

    return parsing_method, time_data_json_dictionary, date_col, time_col, date_format, time_format, csv_file_path

if __name__ == '__main__':
    time_json_file_path = 'mapping_time.json'

    with open(time_json_file_path, 'r') as time_json_file:
        time_data_json = json.load(time_json_file)

    uploaded_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
    if uploaded_files is not None:
        for index, uploaded_file in enumerate(uploaded_files):
            # Save the file temporarily to read it
            csv_file_path = f"temp_{index}.csv"
            with open(csv_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            time_with_each_column_user_input(time_data_json, csv_file_path, index)
