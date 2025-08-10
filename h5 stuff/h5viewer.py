import pandas as pd
import h5py
# Path to the HDF5 file
hdf5_file_path = '../memristor_data3.h5'
#hdf5_file_path = '../memristor_data_backup.h5'

#prints all keys

with h5py.File(hdf5_file_path, "r") as f:
    for key in f.keys():
        print(key)  # Print top-level keys
def print_hdf5_structure(name, obj):
    print(name)  # Print full hierarchical path

with h5py.File(hdf5_file_path, "r") as f:
    f.visititems(print_hdf5_structure)

print("HDF5 structure")


def get_keys_at_depth(store, target_depth=5):
    """
    Recursively traverse the HDF5 file and return keys at the specified depth.

    Parameters:
    - store: h5py.File or h5py.Group object
    - target_depth: int, depth at which to collect keys

    Returns:
    - List of keys at the specified depth
    """

    def traverse(group, current_depth, prefix=""):
        keys = []
        for name in group:
            path = f"{prefix}/{name}".strip("/")
            if isinstance(group[name], h5py.Group):  # If it's a group, recurse
                keys.extend(traverse(group[name], current_depth + 1, path))
            elif isinstance(group[name], h5py.Dataset):  # If it's a dataset, check depth
                if current_depth == target_depth:
                    keys.append(path)
        return keys

    return traverse(store, 1)  # Start at depth 1

# Example usage
with h5py.File(hdf5_file_path, "r") as store:
    keys_at_depth_6 = get_keys_at_depth(store, target_depth=5)

    print(keys_at_depth_6)

def get_data_at_depth(store, target_depth=6):
    """
    Retrieve datasets stored at the specified depth in an HDF5 file.

    Parameters:
    - store: h5py.File or h5py.Group object
    - target_depth: int, depth at which to collect keys and their data_analyzer.py

    Returns:
    - Dictionary where keys are the dataset paths and values are the stored data_analyzer.py
    """
    def traverse(group, current_depth, prefix=""):
        data_dict = {}
        for name in group:
            path = f"{prefix}/{name}".strip("/")
            if isinstance(group[name], h5py.Group):  # If it's a group, recurse
                data_dict.update(traverse(group[name], current_depth + 1, path))
            elif isinstance(group[name], h5py.Dataset):  # If it's a dataset, check depth
                if current_depth == target_depth:
                    data_dict[path] = group[name][()]  # Retrieve data_analyzer.py
        return data_dict

    return traverse(store, 1)  # Start at depth 1

# Example usage
with h5py.File(hdf5_file_path, "r") as store:
    data_at_depth_6 = get_data_at_depth(store, target_depth=5)

# Print keys and sample data_analyzer.py
for key, data in data_at_depth_6.items():
    print(f"Key: {key}, Data Shape: {data.shape if hasattr(data, 'shape') else 'scalar'}, Type: {type(data)}")
    print(data)



# Open the HDF5 file
# with pd.HDFStore(hdf5_file_path, mode='r') as store_path:
#     # List all keys (datasets) in the HDF5 file
#     print("Datasets available in the HDF5 file:")
#     for key in store_path.keys():
#         print(f" - {key}")
#
#     # Load and inspect the data_analyzer.py for each key
#     print("\nInspecting data_analyzer.py from each key:")
#     for key in store_path.keys():
#         print(f"\nKey: {key}")
#
#         # Get information about the stored object
#         storer = store_path.get_storer(key)
#         print(f"Data type of stored object: {type(storer)}")
#
#         # Check if the object is a Frame (DataFrame) or Table
#         if isinstance(storer, pd.io.pytables.FrameFixed):
#             try:
#                 # Load the dataset into a pandas DataFrame
#                 df = store_path.get(key)
#                 print("\nColumns in the DataFrame:")
#                 print(df.columns.tolist())  # Print all column names
#                 print("\nFirst few rows of the DataFrame:")
#                 print(df.head())  # Display the first few rows of the dataset
#             except Exception as e:
#                 print(f"Error loading data_analyzer.py for {key}: {e}")
#         elif isinstance(storer, pd.io.pytables.Table):
#             try:
#                 # If it's a Table, load it as a DataFrame
#                 df = store_path.select(key)
#                 print("\nColumns in the DataFrame:")
#                 print(df.columns.tolist())  # Print all column names
#                 print("\nFirst few rows of the DataFrame:")
#                 print(df.head())  # Display the first few rows of the dataset
#             except Exception as e:
#                 print(f"Error loading data_analyzer.py for {key}: {e}")
#         else:
#             print(f"The object under {key} is not a pandas DataFrame or Table.")
