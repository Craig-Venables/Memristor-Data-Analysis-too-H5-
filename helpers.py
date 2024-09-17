import os
import numpy as np
def split_iv_sweep(filepath):
    """ Read the IV sweep data from a file and return voltage and current arrays. """
    # Add your file reading logic here
    pass

def check_for_loops(v_data):
    """
    :param v_data:
    :return: number of loops for given data set
    """
    # looks at max voltage and min voltage if they are seen more than twice it classes it as a loop
    # checks for the number of zeros 3 = single loop
    num_max = 0
    num_min = 0
    num_zero = 0
    max_v, min_v = bounds(v_data)
    max_v_2 = max_v / 2
    min_v_2 = min_v / 2

    # 4 per sweep
    for value in v_data:
        if value == max_v_2:
            num_max += 1
        if value == min_v_2:
            num_min += 1
        if value == 0:
            num_zero += 1
    # print(num_min)

    # print("num zero", num_zero)
    if num_max + num_min == 4:
        # print("single sweep")
        return 1
    if num_max + num_min == 2:
        # print("half_sweep", num_max, num_min)
        return 0.5
    else:
        # print("multiloop", (num_max + num_min) / 4)
        loops = (num_max + num_min) / 4
        return loops

def extract_folder_names(filepath):
    """ Extract folder names or file metadata from the filepath. """
    # Add your folder extraction logic here
    pass

def filter_positive_values(v_data, c_data):
    """ Filter positive values of voltage and current. """
    return v_data[v_data > 0], c_data[v_data > 0]

def filter_negative_values(v_data, c_data):
    """ Filter negative values of voltage and current. """
    return v_data[v_data < 0], c_data[v_data < 0]

def check_if_folder_exists(base_path, folder_name):
    """ Check if folder exists and create it if not. """
    full_path = os.path.join(base_path, folder_name)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return full_path

def bounds(data):
    """
    :param data:
    :return: max and min values of given array max,min
    """
    max = np.max(data)
    min = np.min(data)
    return max, min

def check_sweep_type(filepath, output_file):
    import re

    def is_number(s):
        """Check if a string represents a number."""
        try:
            float(s)
            return True
        except ValueError:
            return False

    # Open the file at the given filepath
    with open(filepath, 'r', encoding='utf-8') as file:
        # Read the first line and remove any leading/trailing whitespace
        first_line = file.readline().strip()

        if not first_line:
            print("No more lines after the first. Returning None.")
            with open(output_file, 'a', encoding='utf-8') as out_file:
                out_file.write(str(filepath) + '\n')  # Convert filepath to string
            return None

        second_line = file.readline().strip()

        if not second_line:
            with open(output_file, 'a', encoding='utf-8') as out_file:
                out_file.write(str(filepath) + '\n')  # Convert filepath to string
            return None

        nan_check_lines = [file.readline().strip() for _ in range(3)]
        if any('NaN' in line for line in nan_check_lines):
            with open(output_file, 'a', encoding='utf-8') as out_file:
                out_file.write(str(filepath) + '\n')  # Convert filepath to string
            return None

    # Define dictionaries for different types of sweeps and their expected column headings
    sweep_types = {
        'Iv_sweep': [
            ['voltage', 'current'],
            ['vOLTAGE', 'cURRENT'],
            ['VSOURC - Plot 0', 'IMEAS - Plot 0'],
            ['VSOURC - Plot 0\tIMEAS - Plot 0'],
        ],
        'Endurance': ['Iteration #', 'Time (s)', 'Resistance (Set)', 'Set Voltage', 'Time (s)', 'Resistance (Reset)', 'Reset Voltage'],
        'Retention': ['Iteration #', 'Time (s)', 'Current (Set)'],
    }

    for sweep_type, expected_patterns in sweep_types.items():
        for pattern in expected_patterns:
            if all(heading in first_line for heading in pattern):
                if pattern == ['VSOURC - Plot 0', 'IMEAS - Plot 0']:
                    print("Warning: Pattern 3 matched for Iv_sweep. Check data and format.")
                return sweep_type

    first_line_values = first_line.split()
    second_line_values = second_line.split()
    if len(first_line_values) == 2 and len(second_line_values) == 2:
        if is_number(first_line_values[0]) and is_number(first_line_values[1]) and is_number(second_line_values[0]) and is_number(second_line_values[1]):
            return 'Iv_sweep'

    with open(output_file, 'a', encoding='utf-8') as out_file:
        out_file.write(str(filepath) + '\n')  # Convert filepath to string

    return None
