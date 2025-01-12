import pandas as pd
import re
import matplotlib.pyplot as plt

hdf5_file = '../memristor_data.h5'


def analyze_hdf5_levels(hdf5_file, dataframe_type="_info"):
    with pd.HDFStore(hdf5_file, mode='r') as store:
        # Group keys by depth
        grouped_keys = group_keys_by_level(store, max_depth=6)
        #print("Grouped keys by depth:", grouped_keys)  # Debugging output to check the grouped keys

        # Store the data on the first sweeps of devices
        all_first_sweeps = []

        # Analyze data at the lowest level (depth 6) only if necessary
        for key in grouped_keys[5]:
            results = analyze_at_file_level(key, store, dataframe_type)
            if results is not None:
                all_first_sweeps.append(results)

        # First sweep data
        initial_resistance(all_first_sweeps)


def initial_resistance(data):
    resistance_results = []

    for key, value in data:
        #print(f"\nAnalyzing key: {key}")  # Debugging print for each key
        parts = key.strip('/').split('/')
        segments = parts[1].split("-")

        # Extracting the relevant information
        device_number = segments[0]
        concentration = extract_concentration(segments[1])
        btm_e = segments[2]
        polymer, polymer_percent = extract_polymer_info(segments[3])
        top_e = segments[4]

        # Print extracted information for debugging
        print(f"Device Number: {device_number}, Concentration: {concentration}, "
              f"Bottom Electrode: {btm_e}, Polymer: {polymer}, Polymer Percent: {polymer_percent}, "
              f"Top Electrode: {top_e}")

        # Filter data only once
        resistance_data = value[(value['voltage'] >= 0) & (value['voltage'] <= 0.1)]['resistance']

        # Print resistance data for debugging
        #print(f"Resistance Data (0-0.1V) for key {key}:")
        #print(resistance_data)

        resistance = resistance_data.mean()
        # Print calculated resistance for debugging
        print(f"Calculated Average Resistance for key {key}: {resistance}")

        # Store results
        resistance_results.append({
            'device_number': device_number,
            'concentration': concentration,
            'bottom_electrode': btm_e,
            'polymer': polymer,
            'polymer_percent': polymer_percent,
            'top_electrode': top_e,
            'average_resistance': resistance
        })

    resistance_df = pd.DataFrame(resistance_results)

    # Print DataFrame for debugging
    #print("\nResistance DataFrame:")
    #print(resistance_df)

    # Group by device_number
    grouped = resistance_df.groupby('device_number')

    # Compute device statistics
    device_stats = []
    for device, group in grouped:
        resistance = group['average_resistance'].mean()
        max_resistance = group['average_resistance'].max()
        min_resistance = group['average_resistance'].min()
        spread = (max_resistance - min_resistance) / 2

        print(f"\nDevice {device}: Average Resistance: {resistance}, Max Resistance: {max_resistance}, "
              f"Min Resistance: {min_resistance}, Spread: {spread}")

        device_stats.append({
            'device_number': device,
            'average_resistance': resistance,
            'spread': spread
        })

    # Plot results
    device_stats_df = pd.DataFrame(device_stats)
    #print("\nDevice Stats DataFrame:")
    #print(device_stats_df)

    plt.figure(figsize=(10, 6))
    plt.errorbar(
        device_stats_df['device_number'],  # x values
        device_stats_df['average_resistance'],  # y values
        yerr=device_stats_df['spread'],  # Error bars
        fmt='o',
        ecolor='red',
        capsize=5,
        label='Average Resistance with Error'
    )
    plt.xlabel('Device Number')
    plt.ylabel('Average Resistance (Ohms)')
    plt.title('Average Resistance by Device')
    plt.legend()
    plt.grid(True)
    plt.show()


def extract_concentration(concentration):
    match = re.search(r"[\d.]+", concentration)  # Match numbers and decimal points
    if match:
        return float(match.group())  # Convert to float
    return None


def extract_polymer_info(polymer):
    name_match = re.match(r"[A-Za-z]+", polymer)  # Match only letters at the start
    percent_match = re.search(r"\((\d+)%\)", polymer)  # Match the percentage in parentheses
    name = name_match.group() if name_match else None
    percentage = int(percent_match.group(1)) if percent_match else None
    return name, percentage


def group_keys_by_level(store, max_depth=6):
    """
    Group keys by their depth in the hierarchy.
    """
    grouped_keys = {depth: [] for depth in range(1, max_depth + 1)}
    for key in store.keys():
        parts = key.strip('/').split('/')
        depth = len(parts)
        #print(f"Key: {key} -> Parts: {parts}, Depth: {depth}")  # Debugging output
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
        # Debugging output for data preview
        #print(f"\nData for key {file_key}:")
        #print(data.head())

        # find all first files and store for later use
        if filename.startswith('1-'):
            return file_key, data


def filter_keys_by_suffix(keys, suffix):
    """
    Filter keys by a specific suffix (e.g., '_info', '_metrics').
    """
    return [key for key in keys if key.endswith(suffix)]


# Run analysis on _metrics data
analyze_hdf5_levels(hdf5_file, dataframe_type="_metrics")
