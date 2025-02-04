import h5py

def get_data_for_keys(store, keys):
    """
    Retrieve datasets from an HDF5 file using a list of keys.

    Parameters:
    - store: h5py.File object (open in read mode)
    - keys: list of dataset keys (paths in the HDF5 file)

    Returns:
    - Dictionary where keys are dataset paths and values are the stored data
    """
    data_dict = {}
    for key in keys:
        if key in store:  # Check if key exists in the file
            data_dict[key] = store[key][()]  # Retrieve dataset
        else:
            print(f"Warning: Key {key} not found in HDF5 file")
    return data_dict

# Example usage
with h5py.File("pd55.h5", "r") as store:
    keys_at_depth_6 = [...]  # Your list of keys at depth 6
    data_dict = get_data_for_keys(store, keys_at_depth_6)

# Print keys and data information
for key, data in data_dict.items():
    print(f"Key: {key}, Data Shape: {data.shape if hasattr(data, 'shape') else 'scalar'}, Type: {type(data)}")
    print(data)
