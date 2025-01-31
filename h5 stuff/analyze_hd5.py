import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
import h5py
import time
#l
hdf5_file = '../memristor_data.h5'

# todo yield
def analyze_hdf5_levels(hdf5_file, dataframe_type="_info"):
    #with h5py.File(hdf5_file,'r') as store:
    start = time.time()
        #print(store)
    with pd.HDFStore(hdf5_file, mode='r') as store:
        # Group keys by depth
        grouped_keys = group_keys_by_level(store, max_depth=6)
        #print("Grouped keys by depth:", grouped_keys)  # Debugging output to check the grouped keys

        # Store the data on the first sweeps of all devices
        all_first_sweeps = []

        # Analyze data at the lowest level (depth 6) only if necessary
        for key in grouped_keys[5]:
            print(key)
            results = analyze_at_file_level(key, store, dataframe_type)
            #print(results)
            if results is not None:
                all_first_sweeps.append(results)
        middle = time.time()
        #print(all_first_sweeps) # Debug
        # First sweep data
        initial_resistance(all_first_sweeps)
        store.close()

    print("time to organise the data before calling inisital first sweep " , middle-start)

def initial_resistance(data,voltage_val = 0.1):
    """ Finds the initial reseistance between 0-0.1 V for the list of values given
        also filters for data that's not within the list valid_classifications to remove unwanted data
    """

    resistance_results = []
    wrong_classification = []

    # Define valid classifications
    valid_classifications = ["Memristive", "Ohmic","Conductive","intermittent","Mem-Capacitance"]  # Add more classifications here as needed

    for key, value in data:
        """value = all the data (metrics_df)
            key = folder structure"""
        #print('value',value)
        # print(f"\nAnalyzing key: {key}")  # Debugging print for each key
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

        try :
            classification = value['classification'].iloc[0]
        except:
            classification = 'Unknown'
            print(f"No classification found for key {key}")


        if classification in valid_classifications:
            # only work on data that shows memristive or ohmic behaviour
            # Filter data
            # Calculate resistance between the values of V
            resistance_data = value[(value['voltage'] >= 0) & (value['voltage'] <= voltage_val)]['resistance']
            resistance = resistance_data.mean()

            # calculate gradient of line for the data to see difference

            if resistance <0:
                print("check file as classification wrong - negative resistance seen on device")
                #print(key)
                wrong_classification.append(key)

                # maybe if resistance is <0 it should pull the second sweep until a
                # value is found as sometimes the first sweeps non_conductive?

            else:
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
                    'average_resistance': resistance,
                    'classification': classification,
                    'key': key
                })

    resistance_df = pd.DataFrame(resistance_results)

    # Print DataFrame for debugging
    #print("\nResistance DataFrame:")
    #print(resistance_df)

    # Group by device_number
    grouped = resistance_df.groupby('device_number')
    # also plot graph of all the resistances seen within a device and not avaerage them like below

    # Compute device statistics grouped
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

    np.savetxt('wrong_classifications.txt',wrong_classification,fmt='%s')

    device_stats_df = pd.DataFrame(device_stats)
    device_stats_df.to_csv("Average_resistance_device_0.1v.csv", index=False)
    resistance_df.to_csv("resistance_grouped_by_device_0.1v.csv", index=False)


    #plot
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
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('1.png')
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.errorbar(
        resistance_df['device_number'],  # x values
        resistance_df['average_resistance'],  # y values
        fmt='x',
        ecolor='red',
        capsize=5,
        label='Average Resistance'
    )
    plt.xlabel('Device Number')
    plt.ylabel('Average Resistance (Ohms)')
    plt.title('Average Resistance by Device  non averaged')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('2.png')
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.errorbar(
        resistance_df['concentration'],  # x values
        resistance_df['average_resistance'],  # y values
        fmt='x',
        ecolor='red',
        capsize=5,
        label='Average Resistance'
    )
    plt.xlabel('concentration')
    plt.ylabel('Average Resistance (Ohms)')
    plt.title('Average Resistance by Device  non averaged')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('3.png')
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
    Group keys by their depth in the hierarchy. works with pu.h5
    """
    grouped_keys = {depth: [] for depth in range(1, max_depth + 1)}
    for key in store.keys():
        parts = key.strip('/').split('/')
        depth = len(parts)
        #print(f"Key: {key} -> Parts: {parts}, Depth: {depth}")  # Debugging output
        if depth <= max_depth:
            grouped_keys[depth].append(key)

    return grouped_keys

# def group_keys_by_level(store, max_depth=6):
#     """
#     Groups keys in an HDF5 file by their depth in the hierarchy.
#
#     Args:
#         store: An open HDF5 file object.
#         max_depth: The maximum depth to group keys.
#
#     Returns:
#         A dictionary where keys are depths (1 to max_depth) and values are lists of keys at those depths.
#     """
#     grouped_keys = {depth: [] for depth in range(1, max_depth + 1)}
#
#     def recursive_grouping(name, obj, current_depth=1):
#         if current_depth > max_depth:
#             return
#         grouped_keys[current_depth].append(name)
#         if isinstance(obj, h5py.Group):
#             for sub_key in obj.keys():
#                 recursive_grouping(f"{name}/{sub_key}", obj[sub_key], current_depth + 1)
#
#     for key in store.keys():
#         obj = store[key]
#         recursive_grouping(f"/{key}", obj, current_depth=1)
#
#     return grouped_keys

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
