# from datetime import datetime
#
# def observation_mapping (given_list, observation_date_time ,sensor_ID, all_triples, observation_definition,
#                         result_time_term,  has_result_term, has_sim_result_term,
#                         observation_number ,value_from_csv):
#
# ## need to add when there is an sum, max, min, avg observations
#
#     if isinstance(given_list, list):
#         #iterate over the sub items in JSON vocabulary for relavant key
#         for i, sublist in enumerate(given_list):
#
#             if sublist[0] == result_time_term:
#                 #print(f"{i}, a date and time {observation_date_time}")
#                 temp_triple = [observation_definition + str(observation_number), sublist[0],
#                                f'"{observation_date_time.year}-{observation_date_time.month}-{observation_date_time.day}'
#                                f'T{observation_date_time.hour}:{observation_date_time.minute}:{observation_date_time.second}'
#                                f'Z"^^{sublist[-1]}']
#
#             # when the simple result is not a numerical value
#             elif sublist[0] == has_sim_result_term : #and isinstance(sublist, str):
#                 temp_triple = [observation_definition + str(observation_number), sublist[0], '"' +str(value_from_csv) + '"']
#                 #print(f"{i}, a simple results without decimal")
#
#             # when the simple result is a numerical value
#             elif sublist[0][0] == has_sim_result_term:  #and isinstance(sublist, list) and isinstance(sublist[1], list) :
#                 temp_triple = [observation_definition + str(observation_number), sublist[0][0], '"' +str(value_from_csv) + '"' + sublist[1][0] ]
#                 #print(f"{i}, a simple results with decimal")
#
#             # when result is with units
#             elif sublist[0] == has_result_term and isinstance(sublist, list) and isinstance(sublist[1], list) :
#                 #print("Result")
#                 temp_triple = [observation_definition+ str(observation_number), sublist[0],f"""[
#                     {sublist[1][0][0]}  {sublist[1][0][1]};
#                     {sublist[1][1][0]}  {str(value_from_csv)}{sublist[1][1][1]};
#                     {sublist[1][2][0]}  {sublist[1][2][1]}]"""]
#
#             # when the blank nodes are there in results expect for the results
#             elif sublist[0] != has_result_term and isinstance(sublist[-1], str) and sublist[-1].endswith("_"):
#                 #print(f"{i}, when the blank node is {sublist[-1]}")
#                 temp_triple = [observation_definition + str(observation_number), sublist[0], sublist[-1]+str(sensor_ID)]
#
#             # making triples considering only the given two terms in the JSON sublist
#             elif isinstance(sublist[-1],str) and not sublist[-1].endswith("_"):
#                 #print(f"{i}, without blanknodes {sublist[-1]}")
#                 temp_triple = [observation_definition + str(observation_number), sublist[0], sublist[-1]]
#
#             else:
#                 #print("not working",f"for {sublist[-1]}")
#                 temp_triple = []
#
#             all_triples.append(temp_triple)
#
#
#
# if __name__ == "__main__":
#     given_list = [["sosa:observedProperty", "n4e_hyd:AirTemperature2m"],
#                      ["sosa:hasFeatureOfInterest", "n4e_hyd:catchment_" ],
#                      ["sosa:madeBySensor", "n4e_hyd:sensor_"],
#                      ["sosa:resultTime","xsd:dateTime"],
#                      ["sosa:hasResult", "n4e_hyd:temperature2mResult_"],
#                      ["rdf:type","sosa:Result"],
#                      ["cpmeta:hasMaxValue",
#                        [["rdf:type","qudt:numericValue "],
#                       ["qudt:numericValue","^^xsd:decimal"],
#                       ["qudt:unit","unit:DEG_C"]]]]
#
#
#     #element = json_data['observation_designation'][0]
#     value_from_csv = 1.2334
#     has_result_term = "sosa:hasResult"
#     has_sim_result_term = "sosa:hasSimpleResult"
#     result_time_term = "sosa:resultTime"
#     observation_definition = "n4e_hyd:observation_"
#     made_by_sensor_term = "sosa:madeBySensor"
#     number_of_obervations_per_row = 10
#     observation_date_time = datetime(year= 2000, month= 10, day= 14, hour= 11, minute= 9, second= 9)
#     sensor_ID = 1
#     all_triples = []
#     observation_no = 2
#
#     observation_maping(given_list, observation_date_time, sensor_ID, all_triples, observation_definition,result_time_term, has_result_term, has_sim_result_term, observation_no, value_from_csv)
#
#     for triple_subset in all_triples:
#         if len(triple_subset) == 3:
#             triple_1 = triple_subset[0]
#             triple_2 = triple_subset[1]
#             triple_3 = triple_subset[2]
#
#             # Writing the triple to the file in Turtle format
#             print(f"{triple_1} {triple_2} {triple_3} .")
#
#


### new function 2023_05_21
#
# from datetime import datetime
#
# def observation_mapping(given_list, observation_date_time, sensor_ID, all_triples, observation_definition,
#                         result_time_term, has_result_term, has_sim_result_term,
#                         observation_number, value_from_csv):
#     if isinstance(given_list, list):
#         for i, sublist in enumerate(given_list):
#             # Handling result time
#             if sublist[0] == result_time_term:
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0],
#                     f'"{observation_date_time.year}-{observation_date_time.month:02d}-{observation_date_time.day:02d}'
#                     f'T{observation_date_time.hour:02d}:{observation_date_time.minute:02d}:{observation_date_time.second:02d}'
#                     f'Z"^^{sublist[-1]}'
#                 ]
#             # Handling simple result
#             elif sublist[0] == has_sim_result_term:
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0], '"' + str(value_from_csv) + '"'
#                 ]
#             # Handling simple result with nested structure
#             elif isinstance(sublist[0], list) and sublist[0][0] == has_sim_result_term and isinstance(sublist[1], list):
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0][0], '"' + str(value_from_csv) + '"' + sublist[1][0]
#                 ]
#             # Handling complex results with units
#             elif sublist[0] == has_result_term and isinstance(sublist[1], list):
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0],
#                     f"""[
#                     {sublist[1][0][0]}  {sublist[1][0][1]};
#                     {sublist[1][1][0]}  "{str(value_from_csv)}"{sublist[1][1][1]};
#                     {sublist[1][2][0]}  {sublist[1][2][1]}]"""
#                 ]
#             # Handling nested lists like hasMaxValue
#             elif isinstance(sublist[1], list) and isinstance(sublist[1][0], list):
#                 value_node = f"""
#                     {sublist[1][0][0]}  {sublist[1][0][1]};
#                     {sublist[1][1][0]}  "{str(value_from_csv)}"{sublist[1][1][1]};
#                     {sublist[1][2][0]}  {sublist[1][2][1]}
#                 """
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0], f"""[
#                     {value_node.strip()}]"""
#                 ]
#             # Handling blank nodes
#             elif sublist[0] != has_result_term and isinstance(sublist[-1], str) and sublist[-1].endswith("_"):
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0], sublist[-1] + str(sensor_ID)
#                 ]
#             # Handling other cases
#             elif isinstance(sublist[-1], str) and not sublist[-1].endswith("_"):
#                 temp_triple = [
#                     observation_definition + str(observation_number), sublist[0], sublist[-1]
#                 ]
#             else:
#                 temp_triple = []
#
#             if temp_triple:
#                 all_triples.append(temp_triple)
#
#
# if __name__ == "__main__":
#     # given_list = [["sosa:observedProperty", "n4e_hyd:ForecastAlbedo"],
#     #                  ["sosa:hasFeatureOfInterest", "n4e_hyd:catchment_" ],
#     #                  ["sosa:madeBySensor", "n4e_hyd:sensor_"],
#     #                  ["sosa:resultTime","xsd:dateTime"],
#     #                  [["sosa:hasSimpleResult" ], ["^^xsd:decimal"]]]
#
#     given_list = [["sosa:observedProperty", "n4e_hyd:AirTemperature2m"],
#                      ["sosa:hasFeatureOfInterest", "n4e_hyd:catchment_" ],
#                      ["sosa:madeBySensor", "n4e_hyd:sensor_"],
#                      ["sosa:resultTime","xsd:dateTime"],
#                      ["sosa:hasResult", "n4e_hyd:temperature2mResult_"],
#                      ["rdf:type","sosa:Result"],
#                      ["cpmeta:hasMaxValue",
#                        [["rdf:type","qudt:QuantityValue "],
#                       ["qudt:numericValue","^^xsd:decimal"],
#                       ["qudt:unit","unit:DEG_C"]]]]
#
#     value_from_csv = 1.2334
#     has_result_term = "sosa:hasResult"
#     has_sim_result_term = "sosa:hasSimpleResult"
#     result_time_term = "sosa:resultTime"
#     observation_definition = "n4e_hyd:observation_"
#     observation_date_time = datetime(year=2000, month=10, day=14, hour=11, minute=9, second=9)
#     sensor_ID = 1
#     all_triples = []
#     observation_no = 53_2
#
#
#     observation_mapping(given_list, observation_date_time, sensor_ID, all_triples, observation_definition,
#                         result_time_term, has_result_term, has_sim_result_term, observation_no, value_from_csv)
#
#     for triple_subset in all_triples:
#         if len(triple_subset) == 3:
#             triple_1 = triple_subset[0]
#             triple_2 = triple_subset[1]
#             triple_3 = triple_subset[2]
#             print(f"{triple_1} {triple_2} {triple_3} .")


## New function with possible to intergrate sensor ID to observation no

from datetime import datetime
def observation_mapping(given_list, observation_date_time, sensor_ID, all_triples, observation_definition,
                        result_time_term, has_result_term, has_sim_result_term,
                        observation_number, value_from_csv):
    # Ensure observation_number is treated as a string
    observation_number = str(observation_number)

    if isinstance(given_list, list):
        for i, sublist in enumerate(given_list):
            # Handling result time
            if sublist[0] == result_time_term:
                temp_triple = [
                    observation_definition + observation_number, sublist[0],
                    f'"{observation_date_time.year}-{observation_date_time.month:02d}-{observation_date_time.day:02d}'
                    f'T{observation_date_time.hour:02d}:{observation_date_time.minute:02d}:{observation_date_time.second:02d}'
                    f'Z"^^{sublist[-1]}'
                ]
            # Handling simple result
            elif sublist[0] == has_sim_result_term:
                temp_triple = [
                    observation_definition + observation_number, sublist[0], '"' + str(value_from_csv) + '"'
                ]
            # Handling simple result with nested structure
            elif isinstance(sublist[0], list) and sublist[0][0] == has_sim_result_term and isinstance(sublist[1], list):
                temp_triple = [
                    observation_definition + observation_number, sublist[0][0],
                    '"' + str(value_from_csv) + '"' + sublist[1][0]
                ]
            # Handling complex results with units
            elif sublist[0] == has_result_term and isinstance(sublist[1], list):
                temp_triple = [
                    observation_definition + observation_number, sublist[0],
                    f"""[ 
                    {sublist[1][0][0]}  {sublist[1][0][1]};
                    {sublist[1][1][0]}  "{str(value_from_csv)}"{sublist[1][1][1]};
                    {sublist[1][2][0]}  {sublist[1][2][1]}]"""
                ]
            # Handling nested lists like hasMaxValue
            elif isinstance(sublist[1], list) and isinstance(sublist[1][0], list):
                value_node = f"""
                    {sublist[1][0][0]}  {sublist[1][0][1]};
                    {sublist[1][1][0]}  "{str(value_from_csv)}"{sublist[1][1][1]};
                    {sublist[1][2][0]}  {sublist[1][2][1]}
                """
                temp_triple = [
                    observation_definition + observation_number, sublist[0], f"""[ 
                    {value_node.strip()}]"""
                ]
            # Handling blank nodes
            elif sublist[0] != has_result_term and isinstance(sublist[-1], str) and sublist[-1].endswith("_"):
                temp_triple = [
                    observation_definition + observation_number, sublist[0], sublist[-1] + str(sensor_ID)
                ]
            # Handling other cases
            elif isinstance(sublist[-1], str) and not sublist[-1].endswith("_"):
                temp_triple = [
                    observation_definition + observation_number, sublist[0], sublist[-1]
                ]
            else:
                temp_triple = []

            if temp_triple:
                all_triples.append(temp_triple)



if __name__ == "__main__":
    given_list = [["sosa:observedProperty", "n4e_hyd:AirTemperature2m"],
                  ["sosa:hasFeatureOfInterest", "n4e_hyd:catchment_"],
                  ["sosa:madeBySensor", "n4e_hyd:sensor_"],
                  ["sosa:memberOf", "sosa:observationCollection_"],
                  ["sosa:resultTime", "xsd:dateTime"],
                  ["sosa:hasResult", "n4e_hyd:temperature2mResult_"],
                  ["rdf:type", "sosa:Result"],
                  ["cpmeta:hasMaxValue",
                   [["rdf:type", "qudt:QuantityValue "],
                    ["qudt:numericValue", "^^xsd:decimal"],
                    ["qudt:unit", "unit:DEG_C"]]]]

    value_from_csv = 1.2334
    has_result_term = "sosa:hasResult"
    has_sim_result_term = "sosa:hasSimpleResult"
    result_time_term = "sosa:resultTime"
    observation_definition = "n4e_hyd:observation_"
    observation_date_time = datetime(year=2000, month=10, day=14, hour=11, minute=9, second=9)
    sensor_ID = 1
    all_triples = []
    observation_no = "5_32"  # Define it directly as a string with underscores

    observation_mapping(given_list, observation_date_time, sensor_ID, all_triples, observation_definition,
                        result_time_term, has_result_term, has_sim_result_term, observation_no, value_from_csv)

    for triple_subset in all_triples:
        if len(triple_subset) == 3:
            triple_1 = triple_subset[0]
            triple_2 = triple_subset[1]
            triple_3 = triple_subset[2]
            print(f"{triple_1} {triple_2} {triple_3} .")




    # given_list = [["sosa:observedProperty", "n4e_hyd:AirTemperature2m"],
    #               ["sosa:hasFeatureOfInterest", "n4e_hyd:catchment_"],
    #               ["sosa:madeBySensor", "n4e_hyd:sensor_"],
    #               ["sosa:resultTime", "xsd:dateTime"],
    #               ["sosa:hasResult", "n4e_hyd:temperature2mResult_"],
    #               ["rdf:type", "sosa:Result"],
    #               ["cpmeta:hasMaxValue",
    #                [["rdf:type", "qudt:QuantityValue "],
    #                 ["qudt:numericValue", "^^xsd:decimal"],
    #                 ["qudt:unit", "unit:DEG_C"]]]]


