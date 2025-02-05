import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
import h5py
import time
import h5py
#l
hdf5_file = '../memristor_data3.h5'
#hdf5_file = '../memristor_data_backup.h5'

# todo yield


def analyze_hdf5_levels(hdf5_file):

    start = time.time()

    with h5py.File(hdf5_file, "r") as store:

        # Group keys by depth
        grouped_keys = get_keys_at_depth(store, target_depth=5)
        print(grouped_keys)

        # Store the data on the first sweeps of all devices
        all_first_sweeps = []
        all_second_sweeps = []
        all_third_sweeps = []
        all_four_sweeps = []
        all_five_sweeps = []

        # Extract base keys by removing suffixes and co
        base_keys = sorted(set(k.rsplit('_', 2)[0] for k in grouped_keys))

        # Analyze data for each file!
        for base_key in base_keys:
            print(base_key)

            # Retrieve both datasets at once
            df_raw_data, df_file_stats,parts_key = return_data(base_key, store)
            # parts_key = filename(parts[-1]) , device(parts[-2]) etc...


            # store the first five sweeps of any device in a dataframe
            if parts_key[-1].startswith('1-'):
                all_first_sweeps.append((base_key,df_raw_data))
            if parts_key[-1].startswith('2-'):
                all_second_sweeps.append((base_key,df_raw_data))
            if parts_key[-1].startswith('3-'):
                all_third_sweeps.append((base_key,df_raw_data))
            if parts_key[-1].startswith('4-'):
                all_four_sweeps.append((base_key,df_raw_data))
            if parts_key[-1].startswith('5-'):
                all_five_sweeps.append((base_key,df_raw_data))


        middle = time.time()

        print(all_first_sweeps)
        # First sweep data
        initial_resistance(all_first_sweeps)
        store.close()

    print("time to organise the data before calling inisital first sweep ", middle - start)

def initial_resistance(data,voltage_val = 0.1):
    """ Finds the initial reseistance between 0-0.1 V for the list of values given
        also filters for data that's not within the list valid_classifications to remove unwanted data
    """

    resistance_results = []
    wrong_classification = []

    # Define valid classifications
    valid_classifications = ["Memristive", "Ohmic","Conductive","intermittent","Mem-Capacitance"]  # Add more classifications here as needed
    valid_classifications = ["Memristive"]
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



def return_data(base_key, store):
    """
    Given the file key return the data in a pd dataframe converting form numpy array
    """
    parts = base_key.strip('/').split('/')
    print(parts)
    filename = parts[-1]
    device = parts[-2]
    section = parts[-3]

    key_file_stats = base_key+"_file_stats"
    key_raw_data = base_key + "_raw_data"

    data_file_stats = store[key_file_stats][()]
    data_raw_data = store[key_raw_data][()]

    #convert data back to pd dataframe

    column_names_raw_data = ['voltage', 'current', 'abs_current', 'resistance', 'voltage_ps', 'current_ps',
                             'voltage_ng','current_ng', 'log_Resistance', 'abs_Current_ps', 'abs_Current_ng',
                             'current_Density_ps', 'current_Density_ng', 'electric_field_ps', 'electric_field_ng',
                             'inverse_resistance_ps','inverse_resistance_ng', 'sqrt_Voltage_ps', 'sqrt_Voltage_ng',
                             'classification']

    column_names_file_stats = ['ps_area', 'ng_area', 'area', 'normalized_area', 'resistance_on_value',
                               'resistance_off_value', 'ON_OFF_Ratio', 'voltage_on_value', 'voltage_off_value']

    # Convert numpy arrays to pd dataframes
    df_file_stats = pd.DataFrame(data_file_stats, columns=column_names_file_stats)
    df_raw_data_temp = pd.DataFrame(data_raw_data, columns=column_names_raw_data)
    df_raw_data = map_numbers_to_classification(df_raw_data_temp)

    #print(df_file_stats)
    #print(df_raw_data)

    return df_raw_data,df_file_stats,parts



def map_numbers_to_classification(df):
    # Only apply the mapping if the 'classification' column exists in the dataframe
    if 'classification' in df.columns:
        reverse_classification_map = {
            0: 'Memristive',
            1: 'Capacitive',
            2: 'Conductive',
            3: 'Intermittent',
            4: 'Mem-Capacitance',
            5: 'Ohmic',
            6: 'Non-Conductive'
        }
        df['classification'] = df['classification'].map(reverse_classification_map)
    return df

def filter_keys_by_suffix(keys, suffix):
    """
    Filter keys by a specific suffix (e.g., '_info', '_metrics').
    """
    return [key for key in keys if key.endswith(suffix)]

# Run analysis on _metrics data
analyze_hdf5_levels(hdf5_file)