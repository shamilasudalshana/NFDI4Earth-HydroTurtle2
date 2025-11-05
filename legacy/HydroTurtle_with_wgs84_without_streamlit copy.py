import json
import pandas as pd
import time
import os
import re
#from io import StringIO
#from pyproj import Transformer

# Import custom functions
import triple_creation_from_list_function
import Fileter_unique_triples_fucntion
import triple_creation_from_string_function
import observation_mapping_function
import time_variables_creation_from_csv_funtion
import print_RDF_in_turtle_file_fuction
#from extract_sensor_id_from_file_fuciton import extract_sensor_id
#from categorize_file_function import categorize_file
#from check_values_in_a_list_fucntion import check_values_in_list
from format_floats_DF_readed_values_function import format_floats_to_string
#from delimeter_selection_funciton import delimiter_selection
#from transform_coordinates_func import transform_coordinates
#from time_inputs_from_user_management import time_with_each_column_user_input
from time_inputs_from_user_management_without_st import time_with_each_column_user_input_without_st


def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None


def save_file(file_path, content):
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
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
                print(f"Error combining JSON file {file_path}: {e}")
    return combined_data


def process_csv_file(dataframe, mapping_json_data, prefixes_json_data, time_data_json, is_time_dependant_csv,gauge_or_catchment,
                     sensor_ID_column_heading, csv_file_name, parsing_method, date_col, time_col, date_format, time_format):
    all_triples = []

    if sensor_ID_column_heading not in dataframe.columns:
        print(f"Error: Selected sensor ID column '{sensor_ID_column_heading}' does not exist in the DataFrame.")
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

                observation_no = (str(sensor_ID) + '_' + gauge_or_catchment + '_' +
                                  str((index * len(confirmed_matches) + (index_of_iterating_column + 1))))



                observation_date_time = time_variables_creation_from_csv_funtion.parse_csv_row(
                    dataframe, time_data_json, index, parsing_method, date_col, time_col, date_format, time_format)
                observation_mapping_function.observation_mapping(
                    matched_vocabulary_from_mapping_json, observation_date_time, sensor_ID, all_triples,
                    observation_definition, result_time_term, has_result_term, has_sim_result_term,
                    observation_no, cell_value)

    unique_triples = Fileter_unique_triples_fucntion.get_unique_triples(all_triples)
    output_turtle_file = csv_file_name.split(".")[0] + ".ttl"
    print_RDF_in_turtle_file_fuction.write_triples_to_turtle(unique_triples, prefixes_json_data, output_turtle_file)
    print(f"No of inputs converted: {no_of_inputs}")
    return output_turtle_file, len(unique_triples)


def main(csv_file):
    print("Welcome to HydroTurtle - RDF Turtle Converter")

    # Input files
    csv_file_path = csv_file#'ID_32.csv'#input("Enter the path of the CSV file: ")  - csv file
    mapping_json_path = 'mapping_test_5 - CAMEL_GB copy.json'#input("Enter the path of the Mapping JSON file: ") - mapping JSON file
    prefixes_json_path = 'prefixes_dic - Copy.json'#input("Enter the path of the Prefixes JSON file: ") - prefixes dict
    time_data_json_path = "mapping_time.json"  # Time Json file

    # Load files
    csv_data = pd.read_csv(csv_file_path, delimiter=',')
    mapping_json_data = load_json(mapping_json_path)
    prefixes_json_data = load_json(prefixes_json_path)
    time_data_json = load_json(time_data_json_path)

   ## this is to add the column ID from the the name of the file. But this is valid only for the LamaH-CE dataset.
    # Extracting ID from the file name - this is when it runs for a whole folder
    csv_file_name = os.path.basename(csv_file_path)
    # use the below line for LamaH-CE dataset 
    # extracted_id = int(csv_file_name.split("_")[1].split(".")[0]) # this for LamaH-CE dataset

    # use this line for CAMEL-GB dataset 
    searched_id = re.search(r'timeseries_(\d+)_', csv_file_name)
    extracted_id = searched_id.group(1)


    # Adding the ID column
    csv_data['gauge_id'] = extracted_id


    # Time dependency
    is_time_dependant_csv = True #input("Is the dataset time dependent? (yes/no): ").lower() == 'yes' - # variable is assigned as true or fales

    gauge_or_catchment = 'c' # provide 'c' for catchment and provide 'g' for gauge

    sensor_ID_column_heading = 'gauge_id'#("Enter the column name for Sensor IDs: ")
    parsing_method = None
    date_col, time_col, date_format, time_format = None, None, None, None  #CAMELS GB has seperarate date col
    date_col = 'date'  # CAMELS GB has seperarate date col,


    if is_time_dependant_csv:
        parsing_method = "Separate Date and Time Columns"
        parsing_method, time_data_json_dictionary, date_col, time_col, date_format, time_format = time_with_each_column_user_input_without_st(parsing_method ,time_data_json, date_col)
        # date_col = "YYYY" #input("Enter the column name for the Date: ")
        # time_col = input("Enter the column name for the Time: ")
        # date_format = input("Enter the date format (e.g., %Y-%m-%d): ")
        # time_format = input("Enter the time format (e.g., %H:%M:%S): ")


    # to make the timers for the conversion process
    start_time = time.time()

    # Process the CSV file
    result = process_csv_file(csv_data, mapping_json_data, prefixes_json_data, time_data_json,
                              is_time_dependant_csv, gauge_or_catchment, sensor_ID_column_heading, csv_file_path,
                              parsing_method, date_col, time_col, date_format, time_format)

    # stop the timer
    end_time = time.time()

    # time taken for the conversion
    elapsed_time_conversion = end_time - start_time

    if result:
        output_turtle_file, num_triples = result
        print(f"Turtle file created: {output_turtle_file}")
        print(f"Elapsed time: {elapsed_time_conversion:.2f} seconds")
        print(f"Number of triples generated : {num_triples}")


if __name__ == "__main__":

    import glob

    # search all files inside a specific folder
    # *.* means file name with any extension
    dir_path = r'F:\CAMEL_GB_RDF\timeseries/*.*'
    file_list = glob.glob(dir_path)
    print(file_list)

    print(len(file_list))

    for i, csv_file in enumerate(file_list):
        print(f'converting {i+1} file form total {len(file_list)} files')
        main(csv_file)




