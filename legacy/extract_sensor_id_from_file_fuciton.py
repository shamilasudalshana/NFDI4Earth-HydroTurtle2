import re

def extract_sensor_id(file_name):
    match = re.search(r'\d+', file_name)
    if match:
        return int(match.group(0))
    else:
        return None