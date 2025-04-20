import os
import numpy as np
from equations import zero_devision_check
import h5py
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
            ['Voltage', 'Current', 'Time'],
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

def check_for_nan(df):
    if df.isna().values.any():
        print("File contains NaN values. Skipping...")
        return True
    return False

def generate_analysis_params(df, filename, base_dir, device):
    return {
        'df': df,
        'plot_graph': False,
        'save_df': False,
        'device_path': base_dir / device,
        're_save_graph': False,
        'short_name': filename,
        'long_name': f"{filename}.csv"
    }

def extract_file_info(relative_path):
    filename = relative_path.parts[-1]
    device = relative_path.parts[4]
    section = relative_path.parts[3]
    sample = relative_path.parts[2]
    material = relative_path.parts[1]
    return filename, device, section, sample, material

# Print progress every X files
def print_progress(processed_files, total_files, interval):
    if processed_files % interval == 0:
        percent_completed = (zero_devision_check(processed_files, total_files)) * 100
        print(f"Processed {processed_files}/{total_files} files. {percent_completed:.2f}% done.")

# Check if a file already exists in the HDF5
def check_if_file_exists(store_path, key):
    #try:
    with h5py.File(store_path, 'a') as f:  # Open file in append mode
        if key in f:  # Check if key exists in the file
            return True
        else:
            return False


# Generate HDF5 keys for storing data
def generate_hdf5_keys(material, sample, section, device, filename):
    key_info = f'/{material}/{sample}/{section}/{device}/{filename}_file_stats'
    key_metrics = f'/{material}/{sample}/{section}/{device}/{filename}_raw_data'
    return key_info, key_metrics


# def dataframe_to_structured_array(df):
#     """Convert a Pandas DataFrame to a structured NumPy array with HDF5-compatible dtypes."""
#     # Define HDF5-compatible string dtype
#     string_dt = h5py.string_dtype(encoding='utf-8')
#
#     # Convert object columns (strings) to fixed-length UTF-8
#     for col in df.select_dtypes(include=['object']):
#         df[col] = df[col].astype(str)  # Ensure all objects are strings
#         df[col] = df[col].astype(string_dt)  # Convert to HDF5-compatible strings
#
#     # Convert DataFrame to structured NumPy array
#     return np.array(df.to_records(index=False))

def map_classification_to_numbers(df):
    # Only apply the mapping if the 'classification' column exists in the dataframe
    if 'classification' in df.columns:
        classification_map = {
            'Memristive': 0,
            'Capacitive': 1,
            'Conductive': 2,
            'Intermittent': 3,
            'Mem-Capacitance': 4,
            'Ohmic': 5,
            'Non-Conductive': 6
        }
        df['classification'] = df['classification'].map(classification_map)
    return df

def dataframe_to_structured_array(df):
    # Map classification to numbers where applicable
    df = map_classification_to_numbers(df)
    #print(list(df.columns))

    # Define the column data types, ensuring they are compatible with h5py
    dtype = [(col, str) if df[col].dtype == 'object' else (col, df[col].dtype) for col in df.columns]
    #print(df)
    return df.to_numpy()
    #return np.array(df, dtype=dtype)