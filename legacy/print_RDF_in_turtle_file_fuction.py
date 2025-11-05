# to trite triples to a Turtle (.ttl) file.
import mapping_prefixes_fuction

#
# def write_triples_to_turtle(unique_triples_list, prefixes_json, output_file_name):
#
#     # unique_triples_list: A list of triples after deletion of duplicates,
#     # filename: The name of the file to write to.
#
#     with open(output_file_name, 'w') as f:
#
#         # loading variables from prefixes mapping function
#         prefixes_list_used, prefixes = mapping_prefixes_fuction.print_prefixes(prefixes_json, unique_triples_list)
#
#         # printing prefixes
#
#         for prefix in prefixes_list_used:
#             if prefix in prefixes:
#                 f.write(f"@prefix {prefix}: <{prefixes[prefix]}> . \n")
#
#             else:
#                 print(f"Prefix '{prefix}' not found in the Prefixes dictionary JSON file.")
#
#         print(prefixes_list_used)
#
#         # print triples
#         for triple_subset in unique_triples_list:
#             if len(triple_subset) == 3:
#
#                 triple_1 = triple_subset[0]
#                 triple_2 = triple_subset[1]
#                 triple_3 = triple_subset[2]
#
#                 # Writing the triple to the file in Turtle format
#                 f.write(f"{triple_1} {triple_2} {triple_3} .\n")

### new function on 2024_05_01

def write_triples_to_turtle(unique_triples_list, prefixes_json, output_file_name):

    # Load prefixes from the fuction
    prefixes_list_used, prefixes = mapping_prefixes_fuction.print_prefixes(prefixes_json, unique_triples_list)

    # Group triples by subject
    triples_by_subject = {}

    for triple in unique_triples_list:
        if len(triple) == 3:
            subject, predicate, obj = triple

            if subject not in triples_by_subject:
                triples_by_subject[subject] = []

            triples_by_subject[subject].append((predicate, obj))

    with open(output_file_name, 'w') as f:
        # Write prefixes
        for prefix in prefixes_list_used:
            if prefix in prefixes:
                f.write(f"@prefix {prefix}: <{prefixes[prefix]}> .\n")
            else:
                print(f"# Prefix '{prefix}' not found in the Prefixes dictionary JSON file.\n")

        f.write("\n")  # Add a newline after the prefixes

        # Write triples grouped by subject
        for subject, predicates_objects in triples_by_subject.items():
            f.write(f"{subject} ")
            for i, (predicate, obj) in enumerate(predicates_objects):
                if i == len(predicates_objects) - 1:
                    f.write(f"{predicate} {obj} .\n")

                # when the same triple subject is continuing
                else:
                    f.write(f"{predicate} {obj} ;\n\t")

    print(prefixes_list_used)



if __name__ == '__main__':
    unique_triples_list = [
        ['n4e_hyd:sensor_1', 'n4e_hyd:govnrID', '"200014"'],
        ['n4e_hyd:sensor_1', 'schema:name', '"Bangs"'],
        ['n4e_hyd:sensor_1', 'dbo:river', '"Rhein"']
    ]
    prefixes_json = 'prefixes.json'  # Adjust the path to your prefixes JSON file
    output_file_name = 'output_test______.ttl'

    write_triples_to_turtle(unique_triples_list, prefixes_json, output_file_name)

