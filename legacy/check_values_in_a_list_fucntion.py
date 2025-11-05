def check_values_in_list(dictionary, lst):
    for value in dictionary.values():
        if value in lst:
            return True
    return False

if __name__ == '__main__':

    import json

    time_json_path = 'mapping_time.json'

    a = "year"

    with open(time_json_path, 'r') as time_json_file:
        time_data_json = json.load(time_json_file)


    print(type(time_data_json))


    if a in time_data_json:
        print("available")