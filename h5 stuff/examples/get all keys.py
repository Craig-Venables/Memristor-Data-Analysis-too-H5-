

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