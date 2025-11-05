
import streamlit as st
import json
import pandas as pd
from io import StringIO
import time
import geopandas as gpd
from pyproj import Transformer

# Import custom functions
import triple_creation_from_list_function
import Fileter_unique_triples_fucntion
import triple_creation_from_string_function
import observation_mapping_function
import time_variables_creation_from_csv_funtion
import print_RDF_in_turtle_file_fuction
from extract_sensor_id_from_file_fuciton import extract_sensor_id
from categorize_file_function import categorize_file
from check_values_in_a_list_fucntion import check_values_in_list
from format_floats_DF_readed_values_function import format_floats_to_string
from delimeter_selection_funciton import delimiter_selection
from transform_coordinates_func import transform_coordinates, ensure_wgs84
from time_inputs_from_user_management import time_with_each_column_user_input

def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return None


def save_file(file):
    try:
        file_path = file.name
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None


def combine_json_files(json_file_paths):
    combined_data = {}
    for file_path in json_file_paths:
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    combined_data.update(data)
            except Exception as e:
                st.error(f"Error combining JSON file {file_path}: {e}")
    return combined_data


def process_csv_file(dataframe, mapping_json_data, prefixes_json_data, time_data_json, is_time_dependant_csv, gauge_or_catchment,
                     sensor_ID_column_heading, csv_file_name, parsing_method, date_col, time_col, date_format, time_format):
    all_triples = []

    if sensor_ID_column_heading not in dataframe.columns:
        st.error(f"Selected sensor ID column '{sensor_ID_column_heading}' does not exist in the DataFrame.")
        return None

    column_headings = dataframe.columns.tolist()
    confirmed_matches = [key for key in mapping_json_data.keys() if key in column_headings]
    no_of_inputs = 0

    for index, row in dataframe.iterrows():
        sensor_ID = format_floats_to_string(row[sensor_ID_column_heading])
        sensor_designation = mapping_json_data['sensorDesignation'][0] + sensor_ID
        sensor_definition = [sensor_designation, mapping_json_data['sensorDesignation'][1], mapping_json_data['sensorDesignation'][2]]
        all_triples.append(sensor_definition)

        for index_of_iterating_column, heading in enumerate(confirmed_matches):
            cell_value = row[heading]
            no_of_inputs += 1
            matched_vocabulary_from_mapping_json = mapping_json_data[heading]

            if not is_time_dependant_csv:
                element = mapping_json_data['sensorDesignation'][0]
                identification_number = sensor_ID

                if isinstance(matched_vocabulary_from_mapping_json, list):
                    triple_creation_from_list_function.process_given_list(
                        matched_vocabulary_from_mapping_json, element, identification_number, cell_value, all_triples)
                elif isinstance(matched_vocabulary_from_mapping_json, str):
                    triple_creation_from_string_function.process_given_string(
                        matched_vocabulary_from_mapping_json, element, identification_number, cell_value, all_triples)
            else:
                element = mapping_json_data['observation_designation'][0]
                has_result_term = "sosa:hasResult"
                has_sim_result_term = "sosa:hasSimpleResult"
                result_time_term = "sosa:resultTime"
                observation_definition = "hyobs:observation_"

                #observation_no = (index * len(confirmed_matches) + (index_of_iterating_column + 1))

                #updated observation_no including sensor ID
                observation_no = (str(sensor_ID) + '_' + gauge_or_catchment + '_' +
                                  str((index * len(confirmed_matches) + (index_of_iterating_column + 1))))

                observation_date_time = time_variables_creation_from_csv_funtion.parse_csv_row(
                    dataframe, time_data_json, index, parsing_method,date_col, time_col, date_format, time_format)
                observation_mapping_function.observation_mapping(
                    matched_vocabulary_from_mapping_json, observation_date_time, sensor_ID, all_triples,
                    observation_definition, result_time_term, has_result_term, has_sim_result_term,
                    observation_no, cell_value)

    unique_triples = Fileter_unique_triples_fucntion.get_unique_triples(all_triples)
    output_turtle_file = csv_file_name.split(".")[0] + ".ttl"
    print_RDF_in_turtle_file_fuction.write_triples_to_turtle(unique_triples, prefixes_json_data, output_turtle_file)
    st.write(f"No of inputs converted: {no_of_inputs}")
    return output_turtle_file, len(unique_triples)


def home_page():
    st.title("HydroTurtle - RDF Turtle Converter")
    st.image("NFDI4Earth_logo.png", width=450)

    file_type = st.radio("Select file type:", ["CSV", "Shapefile"], index=0)

    if file_type == "CSV":
        csv_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
        mapping_json_files = st.file_uploader("Upload Mapping JSON files", type=['json'], accept_multiple_files=True)
        prefixes_json_files = st.file_uploader("Upload Prefixes JSON files", type=["json"], accept_multiple_files=True)


        if csv_files and mapping_json_files and prefixes_json_files:
            mapping_json_file_paths = [save_file(f) for f in mapping_json_files]
            prefixes_json_file_paths = [save_file(f) for f in prefixes_json_files]
            combined_prefixes_json_data = combine_json_files(prefixes_json_file_paths)

            time_data_json = load_json('mapping_time.json')

            for csv_file_index, csv_file in enumerate(csv_files):
                csv_file_name = csv_file.name
                st.markdown(f"### Processing CSV file: ***{csv_file_name}***")

                # Add dropdown for gauge or catchment
                gauge_or_catchment_selection = st.selectbox(
                    "Select the type of dataset:",
                    options=["gauge", "catchment", "other"],
                    index=0  # Default to "gauge"
                )

                # Assign variable based on selection
                if gauge_or_catchment_selection == "gauge":
                    gauge_or_catchment = "g"
                elif gauge_or_catchment_selection == "catchment":
                    gauge_or_catchment = "c"
                else:
                    gauge_or_catchment = "o"

                st.write(
                    f"Selected type: {gauge_or_catchment_selection.capitalize()} (Assigned as '{gauge_or_catchment.upper()}')")


                selected_mapping_json_file = st.selectbox(f"Select mapping JSON file for {csv_file_name}", mapping_json_file_paths)
                mapping_json_data = load_json(selected_mapping_json_file)
                if f"{csv_file.name}_delimiter" not in st.session_state:
                    st.session_state[f"{csv_file.name}_delimiter"] = ","  # Default delimiter

                delimiter = st.selectbox(
                    f"Select delimiter for {csv_file.name}",
                    [",", ";", "\t", " "],
                    index=[",", ";", "\t", " "].index(st.session_state[f"{csv_file.name}_delimiter"])
                )

                if delimiter != st.session_state[f"{csv_file.name}_delimiter"]:
                    st.session_state[f"{csv_file.name}_delimiter"] = delimiter

                csv_content = csv_file.getvalue().decode("utf-8")
                csv_file_data_frame = pd.read_csv(StringIO(csv_content), delimiter=delimiter)
                st.session_state[f"{csv_file.name}_data_frame"] = csv_file_data_frame

                #st.write(csv_file_data_frame.head())  # Preview the DataFrame

                # Coordinate conversion
                has_coordinates = st.radio(
                    f"Does the dataset '{csv_file.name}' contain coordinates?",
                    options=["Yes", "No"],
                    index=1  # Default to "No"
                ) == "Yes"

                if has_coordinates:
                    is_wgs84_coordinate = st.radio(
                        f"Are the coordinates in '{csv_file.name}' already in WGS 84?",
                        options=["Yes", "No"],
                        index=0
                    ) == "Yes"

                    if not is_wgs84_coordinate:
                        x_col = st.selectbox(f"Select the column for Longitude (x) in '{csv_file.name}':",
                                             csv_file_data_frame.columns)
                        y_col = st.selectbox(f"Select the column for Latitude (y) in '{csv_file.name}':",
                                             csv_file_data_frame.columns)
                        input_epsg = st.text_input(f"Enter the EPSG code of the input CRS (e.g., 3035):", "3035")

                        if st.button(f"Transform Coordinates for {csv_file.name}"):
                            try:
                                transformed_df = transform_coordinates(
                                    csv_file_data_frame, x_col, y_col, f"EPSG:{input_epsg}", "EPSG:4326"
                                )
                                # Store the transformed DataFrame in session state
                                st.session_state[f"{csv_file.name}_data_frame"] = transformed_df
                                st.success(f"Coordinates in '{csv_file.name}' transformed to WGS 84!")
                                st.write(transformed_df.head())  # Preview the transformed DataFrame
                            except Exception as e:
                                st.error(f"Error during transformation: {e}")
                    else:
                        # Save unchanged DataFrame to session state if not already saved
                        if f"{csv_file.name}_data_frame" not in st.session_state:
                            st.session_state[f"{csv_file.name}_data_frame"] = csv_file_data_frame

                ## retrieve the DataFrame from session state
                ##csv_file_data_frame = st.session_state.get(f"{csv_file.name}_data_frame", csv_file_data_frame)
                ##st.write(csv_file_data_frame.head())  # Display the DataFrame to ensure it is retained

                # Time dependency checks
                column_headings = csv_file_data_frame.columns.tolist()
                confirmed_matches = [key for key in mapping_json_file_paths if key in column_headings]
                is_time_dependant_csv = check_values_in_list(dictionary=time_data_json, lst=confirmed_matches)
                st.markdown(f"Is the dataset file '{csv_file.name}' time dependent?")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Confirm '{csv_file.name}' as time dependent"):
                        st.session_state[f"{csv_file.name}_time_dependant"] = True
                        is_time_dependant_csv = True

                with col2:
                    if st.button(f"Confirm '{csv_file.name}' as time independent"):
                        st.session_state[f"{csv_file.name}_time_dependant"] = False
                        is_time_dependant_csv = False
                        st.session_state[f"{csv_file.name}_parsing_method"] = None
                        st.session_state[f"{csv_file.name}_date_col"] = None
                        st.session_state[f"{csv_file.name}_time_col"] = None
                        st.session_state[f"{csv_file.name}_date_format"] = None
                        st.session_state[f"{csv_file.name}_time_format"] = None

                # Ensure session state assignment
                if f"{csv_file.name}_time_dependant" in st.session_state:
                    is_time_dependant_csv = st.session_state[f"{csv_file.name}_time_dependant"]

                if is_time_dependant_csv:
                    st.write(f"The file '{csv_file_name}' is time dependent.")
                    parsing_method, _, date_col, time_col, date_format, time_format, _ = time_with_each_column_user_input(
                        time_data_json, csv_file, csv_content, csv_file_index, delimiter
                    )
                    st.session_state[f"{csv_file.name}_parsing_method"] = parsing_method
                    st.session_state[f"{csv_file.name}_date_col"] = date_col
                    st.session_state[f"{csv_file.name}_time_col"] = time_col
                    st.session_state[f"{csv_file.name}_date_format"] = date_format
                    st.session_state[f"{csv_file.name}_time_format"] = time_format
                else:
                    parsing_method = st.session_state.get(f"{csv_file.name}_parsing_method", None)
                    date_col = st.session_state.get(f"{csv_file.name}_date_col", None)
                    time_col = st.session_state.get(f"{csv_file.name}_time_col", None)
                    date_format = st.session_state.get(f"{csv_file.name}_date_format", None)
                    time_format = st.session_state.get(f"{csv_file.name}_time_format", None)

                sensor_ID_column_heading = st.selectbox("Select the ID column of the sensor/measurement station:", csv_file_data_frame.columns)

                # Use the DataFrame from session state
                csv_file_data_frame = st.session_state[f"{csv_file.name}_data_frame"]
                st.write(csv_file_data_frame.head())  # Verify DataFrame is retained

                if st.button(f"Convert {csv_file.name} to Turtle"):

                    # to make the timers for the conversion process
                    start_time = time.time()

                    result = process_csv_file(
                        csv_file_data_frame, mapping_json_data, combined_prefixes_json_data, time_data_json,
                        is_time_dependant_csv, gauge_or_catchment,sensor_ID_column_heading, csv_file_name, parsing_method, date_col, time_col, date_format, time_format
                    )

                    # stop the timer
                    end_time = time.time()

                    # time taken for the conversion
                    elapsed_time_conversion = end_time - start_time


                    if result:
                        output_turtle_file, num_triples = result
                        st.success(f"Turtle file created: {output_turtle_file}")
                        st.download_button(label="Download Turtle file", data=open(output_turtle_file).read(), file_name=output_turtle_file)
                        st.write(f"Elapsed time: {elapsed_time_conversion:.2f} seconds")
                        st.write(f"Number of triples generated : {num_triples}")


    elif file_type == "Shapefile":

        shapefile = st.file_uploader(

            "Upload a Shapefile (must include all necessary files, e.g., .shp, .dbf, .shx, .prj)", type=["zip"])

        mapping_json_files = st.file_uploader("Upload Mapping JSON files", type=['json'], accept_multiple_files=True)

        prefixes_json_files = st.file_uploader("Upload Prefixes JSON files", type=["json"], accept_multiple_files=True)

        if shapefile and mapping_json_files and prefixes_json_files:

            st.write("Processing shapefile...")

            # Save the uploaded shapefile ZIP locally

            shapefile_path = save_file(shapefile)

            gdf = gpd.read_file(f"zip://{shapefile_path}")

            # Ensure CRS is WGS 84

            gdf = ensure_wgs84(gdf)

            gdf['wkt'] = gdf['geometry'].apply(lambda geom: geom.wkt)

            st.write("Shapefile loaded successfully:")

            st.write(gdf.head())  # Preview GeoDataFrame

            # Save mapping JSON files locally and load them

            mapping_json_file_paths = [save_file(f) for f in mapping_json_files]

            selected_mapping_json_file_path = st.selectbox("Select mapping JSON file for shapefile",
                                                           mapping_json_file_paths)

            mapping_json_data = load_json(selected_mapping_json_file_path)  # Load the selected JSON file

            # Save prefixes JSON files locally and combine them

            prefixes_json_file_paths = [save_file(f) for f in prefixes_json_files]

            combined_prefixes_json_data = combine_json_files(prefixes_json_file_paths)

            sensor_ID_column_heading = st.selectbox("Select the ID column of the sensor/measurement station:",
                                                    gdf.columns)

            parsing_method = None

            date_col = None

            time_col = None

            date_format = None

            time_format = None

            if st.button(f"Convert Shapefile to Turtle"):

                start_time = time.time()

                is_time_dependant_file = False

                guage_or_catchment = None

                # Process shapefile data using process_csv_file function (adjusted for shapefiles)

                result = process_csv_file(

                    gdf, mapping_json_data, combined_prefixes_json_data, None, is_time_dependant_file,

                    guage_or_catchment, sensor_ID_column_heading, shapefile.name, parsing_method,

                    date_col, time_col, date_format, time_format

                )

                end_time = time.time()

                elapsed_time_conversion = end_time - start_time

                if result:
                    output_turtle_file, num_triples = result

                    st.success(f"Turtle file created: {output_turtle_file}")

                    st.download_button(label="Download Turtle file", data=open(output_turtle_file).read(),

                                       file_name=output_turtle_file)

                    st.write(f"Elapsed time: {elapsed_time_conversion:.2f} seconds")

                    st.write(f"Number of triples generated: {num_triples}")


def main():
    st.sidebar.title("Navigation Panel")
    page = st.sidebar.radio("Go to", ['Home', 'Settings', 'About'])

    if page == "Home":
        home_page()
    elif page == "Settings":
        st.write("Settings page")
    elif page == "About":
        st.write("About page")


if __name__ == "__main__":
    main()

