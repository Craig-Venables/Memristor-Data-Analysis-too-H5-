def get_data_at_depth(store, target_depth=6):
    """
    Retrieve datasets stored at the specified depth in an HDF5 file.

    Parameters:
    - store: h5py.File or h5py.Group object
    - target_depth: int, depth at which to collect keys and their data

    Returns:
    - Dictionary where keys are the dataset paths and values are the stored data
    """
    def traverse(group, current_depth, prefix=""):
        data_dict = {}
        for name in group:
            path = f"{prefix}/{name}".strip("/")
            if isinstance(group[name], h5py.Group):  # If it's a group, recurse
                data_dict.update(traverse(group[name], current_depth + 1, path))
            elif isinstance(group[name], h5py.Dataset):  # If it's a dataset, check depth
                if current_depth == target_depth:
                    data_dict[path] = group[name][()]  # Retrieve data
        return data_dict

    return traverse(store, 1)  # Start at depth 1

# Example usage
with h5py.File(hdf5_file_path, "r") as store:
    data_at_depth_6 = get_data_at_depth(store, target_depth=5)

# Print keys and sample data
for key, data in data_at_depth_6.items():
    print(f"Key: {key}, Data Shape: {data.shape if hasattr(data, 'shape') else 'scalar'}, Type: {type(data)}")