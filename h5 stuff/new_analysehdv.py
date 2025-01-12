import pandas as pd
import matplotlib.pyplot as plt

# Path to the HDF5 file
hdf5_file = '../memristor_data.h5'


def analyze_hdf5_levels(hdf5_file, dataframe_type="_info"):
    with pd.HDFStore(hdf5_file, mode='r') as store:
        # Group keys by depth
        grouped_keys = group_keys_by_level(store, max_depth=6)
        # Analyze data at the lowest level (depth 6)
        all_first_sweeps = []
        for key in grouped_keys[5]:
            first_sweep_data = analyze_at_file_level(key, store, dataframe_type)
            if first_sweep_data is not None:
                all_first_sweeps.append(first_sweep_data)

        # Combine all first sweep data and plot
        if all_first_sweeps:
            combined_data = pd.concat(all_first_sweeps, ignore_index=True)
            plot_first_sweep_data(combined_data)


def group_keys_by_level(store, max_depth=6):
    """
    Group keys by their depth in the hierarchy.
    """
    grouped_keys = {depth: [] for depth in range(1, max_depth + 1)}
    for key in store.keys():
        parts = key.strip('/').split('/')
        depth = len(parts)
        if depth <= max_depth:
            grouped_keys[depth].append(key)
    return grouped_keys


def analyze_at_file_level(file_key, store, dataframe_type="_info"):
    """
    Perform analysis at the file level, specifically targeting '_info' or '_metrics' dataframes.
    """
    parts = file_key.strip('/').split('/')
    filename = parts[-1]

    if not file_key.endswith(dataframe_type):
        target_key = f"{file_key}{dataframe_type}"
    else:
        target_key = file_key

    if target_key in store.keys():
        data = store[target_key]
        if filename.startswith('1-'):
            return get_first_sweep_data(data)
    return None


def get_first_sweep_data(data):
    """
    Extract resistance values from the first sweeps.
    """
    if "resistance" in data.columns:
        return data
    else:
        print("No resistance data found in the provided DataFrame.")
        return None


def plot_first_sweep_data(data):
    """
    Plot resistance values against concentration.
    """

    print(data)
    # Assuming a 'concentration' column exists in the data
    # if "concentration" in data.columns:
    #     plt.figure(figsize=(10, 6))
    #     for conc, group in data.groupby("concentration"):
    #         plt.plot(group.index, group["resistance"], label=f"Concentration: {conc}")
    #     plt.xlabel("Index")
    #     plt.ylabel("Resistance (Ohms)")
    #     plt.title("Resistance vs Concentration for First Sweeps")
    #     plt.legend()
    #     plt.grid()
    #     plt.show()
    # else:
    #     print("No 'concentration' column in data. Cannot plot.")


# Analyze all _metrics data at each level
analyze_hdf5_levels(hdf5_file, dataframe_type="_metrics")
