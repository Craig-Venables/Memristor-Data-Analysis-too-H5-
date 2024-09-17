import os

def split_iv_sweep(filepath):
    """ Read the IV sweep data from a file and return voltage and current arrays. """
    # Add your file reading logic here
    pass

def check_for_loops(v_data):
    """ Check if the voltage data contains multiple sweeps (loops). """
    # Add logic to detect loops here
    pass

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
