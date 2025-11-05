import json
import pandas as pd
from io import StringIO
def time_with_each_column_user_input_without_st(parsing_method, time_data_json_dictionary, date_column = None, time_column = None):
    # Initialize default values
    #parsing_method = "Separate Columns for Year/Month/Day/Hour/Minute/Second"  # Options: "Separate Columns for Year/Month/Day/Hour/Minute/Second", "Combined Date and Time Column", "Separate Date and Time Columns"
    date_col = None
    time_col = None
    date_format = None
    time_format = None

    if parsing_method == "Separate Date and Time Columns":
        date_col = date_column #"Date_Column_Name"  # Replace with actual column name for the date
        time_col = time_column #"Time_Column_Name"  # Replace with actual column name for the time or "Not Applicable"

        if time_col == "Not Applicable":
            time_col = None

        # Choose from common date and time formats
        common_date_formats = [
            "%d:%m:%Y", "%d/%m/%Y", "%m-%d-%Y", "%Y.%m.%d", "%Y-%m-%d"
        ]
        common_time_formats = [
            "%H:%M:%S", "%H/%M/%S", "%I:%M:%S %p", "%H.%M.%S"
        ]
        date_format = "%Y-%m-%d"  # Replace with the desired date format
        time_format = "%H:%M:%S"  # Replace with the desired time format

    elif parsing_method == "Separate Columns for Year/Month/Day/Hour/Minute/Second":
        # Initialize the variables list for the time and date related from the keys of time_data_json
        time_date_dictionary_keys = ["year", "month", "day", "hour", "minute", "second", "dateOfYear"]

        # Replace with a mapping of keys to column names or "Not Applicable"
        column_mapping = {
            "year": "YYYY",  # Replace with the actual column name for "year" or "Not Applicable"
            "month": "MM",  # Similarly replace for each key
            "day": "DD",
            "hour": "Not Applicable",
            "minute": "Not Applicable",
            "second": "Not Applicable",
            "dateOfYear": "DOY"
        }

        # Loop through each variable and update the dictionary
        for variable in time_date_dictionary_keys:
            col_heading = column_mapping.get(variable, "Not Applicable")
            if col_heading != "Not Applicable":
                time_data_json_dictionary[variable] = col_heading

        date_col, time_col, date_format, time_format = None, None, None, None

    elif parsing_method == 'Combined Date and Time Column':
        date_col = "Combined_Column_Name"  # Replace with actual combined date and time column name
        time_col = None

        common_datetime_formats = [
            "%d:%m:%Y %H:%M:%S", "%d/%m/%Y %H/%M/%S", "%m/%d/%Y %H/%M/%S", "%m-%d-%Y %H:%M:%S",
            "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"
        ]
        date_format = "%d:%m:%Y %H:%M:%S"  # Replace with the desired datetime format
        time_format = None  # Not needed for combined date and time column

    else:
        print("This is still in progress.")
        date_col, time_col, date_format, time_format = None, None, None, None

    print(f"data format : {date_format} and date column: {date_column}")
    return parsing_method, time_data_json_dictionary, date_col, time_col, date_format, time_format


if __name__ == '__main__':
    time_json_file_path = 'mapping_time.json'

    with open(time_json_file_path, 'r') as time_json_file:
        time_data_json = json.load(time_json_file)

    # Example DataFrame for testing
    csv_data = {
        "Year_Column_Name": [2023],
        "Month_Column_Name": [12],
        "Day_Column_Name": [3],
        "Hour_Column_Name": [15],
        "Minute_Column_Name": [45],
        "Second_Column_Name": [30]
    }
    csv_file_data_frame = pd.DataFrame(csv_data)

    file_index = 0
    delimiter = ","

    result = time_with_each_column_user_input_without_st(time_data_json, csv_file_data_frame, file_index, delimiter)
    print(result)
