def process_given_string(given_string, element, identification_no, value_from_csv, all_triples):
    temp_triple = [element + str(identification_no), given_string, '"' + str(value_from_csv) + '"']

    all_triples.append(temp_triple)