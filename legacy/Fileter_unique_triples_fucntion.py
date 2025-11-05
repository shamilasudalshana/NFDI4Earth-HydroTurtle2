def get_unique_triples(all_triples):
    seen = set()
    unique_triples = []

    for triple in all_triples:
        #print(triple)
        triple_tuple = tuple(triple)
        if triple_tuple not in seen:
            unique_triples.append(triple)
            seen.add(triple_tuple)

    return unique_triples