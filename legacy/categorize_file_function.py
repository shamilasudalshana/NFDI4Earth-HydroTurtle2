
def categorize_file(file_name):
    if 'obs' in file_name.lower():
        return 'Observation File'
    elif 'catch' in file_name.lower() and 'att' in file_name.lower():
        return 'Catchment Attribute File'
    elif 'gau' in file_name.lower() and 'att' in file_name.lower():
        return 'Gauge Attribute File'
    else:
        return 'Unknown File Type'