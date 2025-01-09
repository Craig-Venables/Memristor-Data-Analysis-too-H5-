import pandas as pd

# Path to the HDF5 file
hdf5_file = '../memristor_data.h5'


def analyze_hdf5_levels(hdf5_file, dataframe_type="_info"):
    with pd.HDFStore(hdf5_file, mode='r') as store:
        # Group keys by depth
        grouped_keys = group_keys_by_level(store, max_depth=6)
        #print(grouped_keys)  # Debugging output to check the grouped keys

        # Analyze data at the lowest level (depth 6)
        for key in grouped_keys[5]:
            #print(f"Analyzing key: {key}")
            analyze_at_file_level(key, store, dataframe_type,)


def group_keys_by_level(store, max_depth=6):
    """
    Group keys by their depth in the hierarchy.
    """
    grouped_keys = {depth: [] for depth in range(1, max_depth + 1)}
    for key in store.keys():
        parts = key.strip('/').split('/')
        depth = len(parts)
        print("parts",parts)
        # print(f"Key: {key} -> Parts: {parts}, Depth: {depth}")  # Debugging output
        if depth <= max_depth:
            grouped_keys[depth].append(key)

    return grouped_keys


def analyze_at_file_level(file_key, store, dataframe_type="_info"):
    """
    Perform analysis at the file level, specifically targeting '_info' or '_metrics' dataframes.
    """
    parts = file_key.strip('/').split('/')
    filename = parts[-1]
    device = parts[-2]
    section = parts[-3]

    if not file_key.endswith(dataframe_type):
        target_key = f"{file_key}{dataframe_type}"
    else:
        target_key = file_key

    if target_key in store.keys():
        data = store[target_key]
        print(f"Data for file {target_key}:")
        #print(data.head())


        # Calculate resistance for filenames starting with "1-"
        if filename.startswith('1-'):
            print(data["resistance"])

            # save data for use later


        # Add file-level analysis logic
    #else:
        #print(f"Target key {target_key} not found in the HDF5 store.")




# To filter keys that are relevant (e.g., only '_info' or '_metrics')
def filter_keys_by_suffix(keys, suffix):
    """
    Filter keys by a specific suffix (e.g., '_info', '_metrics').
    """
    return [key for key in keys if key.endswith(suffix)]


# Analyze all _info data at each level
# analyze_hdf5_levels(hdf5_file, dataframe_type="_info")

# Analyze all _metrics data at each level
analyze_hdf5_levels(hdf5_file, dataframe_type="_metrics")

