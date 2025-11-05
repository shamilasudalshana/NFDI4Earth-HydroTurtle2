def process_given_list(given_list, element, identification_no, value_from_csv, all_triples):
    previous_blank_node = None

    temporary_triples = []
    has_previous_bank_node = False

    for i, sublist in enumerate(given_list):

        #print(f"current sublist: {sublist}")
        # if len(sublist) < 2:
        #    print(f"Warning: Sublist at index {i} does not have enough elements.")
        #    continue

        if i == 0:  # First sublist handling
            if len(sublist[-1]) > 0 and isinstance(sublist[-1],str) and sublist[-1].endswith("_"):
                temp_triple = [element + str(identification_no), sublist[0], sublist[1] + str(identification_no)]
                previous_blank_node = sublist[1] + str(identification_no)

                has_previous_bank_node = True

            else:
                temp_triple = [element + str(identification_no), sublist[0][0], '"' + str(value_from_csv) + '"' +str(sublist[-1][0])]


        if i != 0 and i == len(given_list) - 1:  # last sublist handling

            if len(sublist) == 1:
                temp_triple = [temp_triple[0], sublist[0], '"' + str(value_from_csv) + '"']

            if isinstance(sublist[-1], list) and len(sublist[-1]) == 3:
                temp_triple = [temp_triple[0], sublist[0],f"""[
                    {sublist[1][0][0]}  {sublist[1][0][1]};
                    {sublist[1][1][0]}  "{str(value_from_csv)}"{sublist[1][1][1]};
                    {sublist[1][2][0]}  {sublist[1][2][1]}]"""]

            elif len(sublist) == 2 and has_previous_bank_node == True:
                temp_triple = [previous_blank_node, sublist[0][0], '"' + str(value_from_csv) + '"' +str(sublist[1][0])]

            elif len(sublist) == 2 and has_previous_bank_node == False:
                temp_triple = [temp_triple[0], sublist[0][0], '"' + str(value_from_csv) + '"' +str(sublist[1][0])]


        if i != 0 and i != len(given_list) - 1 :


            if len(sublist[-1]) > 0 and sublist[-1].endswith("_"):
                temp_triple = [previous_blank_node, sublist[0], sublist[1] + str(identification_no)]

                #previous_blank_node = sublist[1] + str(identification_no)

                has_previous_bank_node = True
                #print("test2")

            elif previous_blank_node:
                temp_triple = [previous_blank_node, sublist[0], sublist[1]]


        all_triples.append(temp_triple)
        if len(sublist) > 1 and len(sublist[-1]) > 0 and isinstance(sublist[-1], str) and sublist[-1].endswith("_"):
            previous_blank_node = sublist[1] + str(identification_no)

        #else:
            #print("no change")
            #previous_blank_node = None  # Reset previous_blank_node if the current element does not end with "_"

        #print(temp_triple)


    return all_triples

if __name__ == "__main__":
    given_list  = [["n4e_hyd:hasSoil","n4e_hyd:soil_"],
                  ["rdf:type", "envthes:24"],
                  ["n4e_hyd:hasRootdepth","n4e_hyd:rootdepth_"],
                  ["rdf:type", "n4e_hyd:RootDepth"],
                  ["owl:hasValue",
                    [["rdf:type","qudt:numericValue "],
                      ["qudt:numericValue","^^xsd:decimal"],
                      ["qudt:unit","unit:M"]]]]
    element = "n4e_hyd:sensor_"
    identification_no = 1
    value_from_csv = 4668.379
    all_triple = []

    all_triple = process_given_list(given_list, element, identification_no, value_from_csv, all_triple)

    for triple_subset in all_triple:
        if len(triple_subset) == 3:
            triple_1 = triple_subset[0]
            triple_2 = triple_subset[1]
            triple_3 = triple_subset[2]

            # Writing the triple to the file in Turtle format
            print(f"{triple_1} {triple_2} {triple_3} .\n")

    print(all_triple)