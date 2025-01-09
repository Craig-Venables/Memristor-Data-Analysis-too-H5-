import h5py
import numpy as np


def load_data_from_h5(file, key):
    """
    Function to load data from an H5 file given a specific key (path in the file).
    We check if the key corresponds to a group or dataset and handle it accordingly.
    """
    try:
        # Check if the key corresponds to a dataset
        if isinstance(file[key], h5py.Dataset):
            data = file[key][()]  # Load data associated with the given key
        else:
            # If the key is a group, print a message and return an empty list or handle it accordingly
            print(f"Warning: {key} is a group, not a dataset. Skipping.")
            data = []
    except KeyError:
        print(f"KeyError: {key} not found in the file.")
        data = []

    return data


def analyze_data_by_level(file_path, level='sample'):
    """
    Function to analyze data at a specific level (e.g., sample, section, device).
    """
    with h5py.File(file_path, 'r') as f:
        all_keys = list(f.keys())  # Get all keys (paths in the file)

        # Debugging: Print out the keys to verify their structure
        print("Keys in the HDF5 file:")
        for key in all_keys:
            print(key)

        # Group data by the specified level (sample, section, or device)
        grouped_data = group_data_by_level(all_keys, level, f)

        # Analyze data based on the level
        if level == 'sample':
            analyzed_data = analyze_sample(grouped_data)
        elif level == 'section':
            analyzed_data = analyze_section(grouped_data)
        elif level == 'device':
            analyzed_data = analyze_device(grouped_data)
        else:
            raise ValueError("Unsupported level for analysis")

        return analyzed_data


def group_data_by_level(all_keys, level, f):
    """
    Function to group data by the specified level (sample, section, or device).
    This version assumes that the keys are simple (material, sample) without further sublevels.
    Now, the file object is passed directly to load the data.
    """
    grouped_data = {}

    # In this case, each key is just a material/sample and doesn't have further sublevels
    for key in all_keys:
        parts = key.split('/')  # Split the key by '/'

        # If there are no further parts, consider the entire key as a group
        group = parts[0]  # In this case, it's just the first part (sample or material name)

        # Add data to the corresponding group
        if group not in grouped_data:
            grouped_data[group] = []

        # Load data from the file using the passed file object
        data = load_data_from_h5(f, key)
        grouped_data[group].append(data)

    return grouped_data


def analyze_sample(grouped_data):
    """
    Function to analyze data at the sample level.
    Example: Compare or summarize data for each sample.
    """
    analyzed_data = {}
    for sample, data_list in grouped_data.items():
        # Example analysis: average data across all devices in this sample
        analyzed_data[sample] = np.mean(data_list, axis=0)

    return analyzed_data


def analyze_section(grouped_data):
    """
    Function to analyze data at the section level.
    Example: Compare or summarize data for each section.
    """
    analyzed_data = {}
    for section, data_list in grouped_data.items():
        # Example analysis: average data across all devices in this section
        analyzed_data[section] = np.mean(data_list, axis=0)

    return analyzed_data


def analyze_device(grouped_data):
    """
    Function to analyze data at the device level.
    Example: Compare or summarize data for each device.
    """
    analyzed_data = {}
    for device, data_list in grouped_data.items():
        # Example analysis: average data for this specific device
        analyzed_data[device] = np.mean(data_list, axis=0)

    return analyzed_data


# Example usage:
file_path = '../memristor_data.h5'

# For sample-level analysis
sample_result = analyze_data_by_level(file_path, level='sample')
print("Sample-level analysis:", sample_result)

# For section-level analysis
section_result = analyze_data_by_level(file_path, level='section')
print("Section-level analysis:", section_result)

# For device-level analysis
device_result = analyze_data_by_level(file_path, level='device')
print("Device-level analysis:", device_result)
