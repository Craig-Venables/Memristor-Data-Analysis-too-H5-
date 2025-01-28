import h5py
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

hdf5_file = '../memristor_data.h5'


def analyze_hdf5_levels(hdf5_file, dataframe_type="_info"):
    """
    Analyze data from an HDF5 file by grouping keys by depth and processing the data.
    """
    with h5py.File(hdf5_file, 'r') as store:
        def print_structure(name, obj):
            print(f"{name}: {type(obj)}")

        store.visititems(print_structure)

        #store.visit(print)  # Print all keys in the HDF5 file
        # Group keys by depth
        grouped_keys = group_keys_by_level(store, max_depth=6)
        #print("Grouped keys by depth:", grouped_keys)  # Debugging output to check the grouped keys

        # Store the data on the first sweeps of all devices
        all_first_sweeps = []

        # Analyze data at the lowest level (depth 6) only if necessary
        if 5 in grouped_keys:  # Ensure depth 6 exists
            for key in grouped_keys[5]:
                #print(f"Analyzing key: {key}")
                results = analyze_at_file_level(key, store, dataframe_type)
                print(results)
                if results is not None:
                    all_first_sweeps.append(results)

        # Perform analysis on the first sweep data
        initial_resistance(all_first_sweeps)


def initial_resistance(data, voltage_val=0.1):
    """
    Finds the initial resistance between 0-0.1 V for the given list of values.
    """
    resistance_results = []
    wrong_classification = []

    # Define valid classifications
    valid_classifications = ["Memristive", "Ohmic", "Conductive", "Intermittent", "Mem-Capacitance"]

    for key, value in data:
        # Extract metadata from the key
        parts = key.strip('/').split('/')
        segments = parts[1].split("-")

        print("value",value)

        device_number = segments[0]
        concentration = extract_concentration(segments[1])
        btm_e = segments[2]
        polymer, polymer_percent = extract_polymer_info(segments[3])
        top_e = segments[4]

        try:
            classification = value['classification'][0]
        except KeyError:
            classification = 'Unknown'
            print(f"No classification found for key {key}")

        if classification in valid_classifications:
            resistance_data = value[(value['voltage'] >= 0) & (value['voltage'] <= voltage_val)]['resistance']
            resistance = resistance_data.mean()

            if resistance < 0:
                print("Check file as classification is wrong - negative resistance seen on device.")
                print(key)
                wrong_classification.append(key)
            else:
                resistance_results.append({
                    'device_number': device_number,
                    'concentration': concentration,
                    'bottom_electrode': btm_e,
                    'polymer': polymer,
                    'polymer_percent': polymer_percent,
                    'top_electrode': top_e,
                    'average_resistance': resistance,
                    'classification': classification
                })

    # Save results and create output
    resistance_df = pd.DataFrame(resistance_results)
    print("resistance results",resistance_results)
    grouped = resistance_df.groupby('device_number')

    device_stats = []
    for device, group in grouped:
        resistance = group['average_resistance'].mean()
        max_resistance = group['average_resistance'].max()
        min_resistance = group['average_resistance'].min()
        spread = (max_resistance - min_resistance) / 2

        device_stats.append({
            'device_number': device,
            'average_resistance': resistance,
            'spread': spread
        })

    # Save outputs
    np.savetxt('wrong_classifications.txt', wrong_classification, fmt='%s')
    device_stats_df = pd.DataFrame(device_stats)
    device_stats_df.to_csv("Average_resistance_device_0.1v.csv", index=False)
    resistance_df.to_csv("resistance_grouped_by_device_0.1v.csv", index=False)

    # Plot results
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        device_stats_df['device_number'],
        device_stats_df['average_resistance'],
        yerr=device_stats_df['spread'],
        fmt='o',
        ecolor='red',
        capsize=5,
        label='Average Resistance with Error'
    )
    plt.xlabel('Device Number')
    plt.ylabel('Average Resistance (Ohms)')
    plt.title('Average Resistance by Device')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.show()


def extract_concentration(concentration):
    """
    Extract numerical concentration value from a string.
    """
    match = re.search(r"[\d.]+", concentration)
    return float(match.group()) if match else None


def extract_polymer_info(polymer):
    """
    Extract polymer name and percentage from a string.
    """
    name_match = re.match(r"[A-Za-z]+", polymer)
    percent_match = re.search(r"\((\d+)%\)", polymer)
    name = name_match.group() if name_match else None
    percentage = int(percent_match.group(1)) if percent_match else None
    return name, percentage


def group_keys_by_level(store, max_depth=6):
    """
    Group keys in an HDF5 file by their depth in the hierarchy.

    Args:
        store: An open HDF5 file object.
        max_depth: The maximum depth to group keys.

    Returns:
        A dictionary where keys are depths (1 to max_depth) and values are lists of keys at those depths.
    """
    grouped_keys = {depth: [] for depth in range(1, max_depth + 1)}

    def recursive_grouping(name, obj, current_depth=1):
        if current_depth > max_depth:
            return
        grouped_keys[current_depth].append(name)
        if isinstance(obj, h5py.Group):
            for sub_key in obj.keys():
                recursive_grouping(f"{name}/{sub_key}", obj[sub_key], current_depth + 1)

    for key in store.keys():
        recursive_grouping(f"/{key}", store[key], current_depth=1)

    return grouped_keys


def analyze_at_file_level(file_key, store, dataframe_type="_info"):
    """
    Perform analysis at the file level, specifically targeting '_info' or '_metrics' datasets.
    """
    print(f"Processing file key: {file_key}")  # Debugging

    # Construct the target key
    if not file_key.endswith(dataframe_type):
        target_key = f"{file_key}{dataframe_type}"
    else:
        target_key = file_key

    # Check if the target key exists
    if target_key in store:
        obj = store[target_key]
        print(f"Found target key: {target_key}")  # Debugging

        # Check if the target key is a group
        if isinstance(obj, h5py.Group):
            print(f"Target key {target_key} is a group. Traversing its contents.")  # Debugging
            datasets = []
            obj.visititems(lambda name, node: datasets.append(name) if isinstance(node, h5py.Dataset) else None)

            # Process each dataset in the group
            for dataset_name in datasets:
                dataset_key = f"{target_key}/{dataset_name}"  # Full path to the dataset
                print(f"Processing dataset: {dataset_key}")  # Debugging
                data = store[dataset_key][()]  # Load dataset as a NumPy array

                # Convert to DataFrame if this is the first sweep (filename starts with '1-')
                if file_key.split('/')[-1].startswith('1-'):
                    df = pd.DataFrame(data)
                    print(f"Extracted DataFrame for dataset {dataset_key}:\n{df.head()}")  # Debugging
                    return file_key, df

        elif isinstance(obj, h5py.Dataset):
            print(f"Target key {target_key} is a dataset.")  # Debugging
            data = obj[()]  # Load dataset as a NumPy array

            # Convert to DataFrame if this is the first sweep (filename starts with '1-')
            if file_key.split('/')[-1].startswith('1-'):
                df = pd.DataFrame(data)
                print(f"Extracted DataFrame for dataset {target_key}:\n{df.head()}")  # Debugging
                return file_key, df

        else:
            print(f"Target key {target_key} is neither a group nor a dataset.")  # Debugging
    else:
        print(f"Target key {target_key} not found in the HDF5 file.")  # Debugging

    return None

def filter_keys_by_suffix(keys, suffix):
    """
    Filter keys by a specific suffix (e.g., '_info', '_metrics').
    """
    return [key for key in keys if key.endswith(suffix)]


# Run analysis on _metrics data
if __name__ == "__main__":
    analyze_hdf5_levels(hdf5_file, dataframe_type="_metrics")
