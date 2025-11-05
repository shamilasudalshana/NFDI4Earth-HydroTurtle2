import pandas as pd

# function to convert the value to string while preserving its format
# this is mainly when the cell value can have both integers and strings only need to convert floats without decimals

def format_floats_to_string(value):
    if pd.isna(value): # to check whether the Not a number
        return ''

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)

if __name__ == "__main__":

    test = format_floats_to_string('24.0')

    print(test)