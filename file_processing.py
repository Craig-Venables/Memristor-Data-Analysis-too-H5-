import pandas as pd
import sys
import h5py
from equations import absolute_val, current_density_eq, resistance, electric_field_eq, inverse_resistance_eq, \
    sqrt_array, zero_devision_check,log_value,filter_positive_values,filter_negative_values
import equations as eq
from metrics_calculation import calculate_metrics_for_loops, area_under_curves, on_off_values
from plotting import plot_loop_data, plot_single_sweep_data
from helpers import check_for_loops, extract_folder_names, check_if_folder_exists,split_iv_sweep,dataframe_to_structured_array


def file_analysis(df, plot_graph, save_df, device_path, re_save_graph, short_name, long_name):
    """ Analyze a single file, calculate metrics, and return a DataFrame for storage """

    # You already have the DataFrame passed in, so no need to read it from the file
    #print(f"Columns in the DataFrame: {df.columns}")
    # Step 1: Preprocess voltage and current data_analyzer.py from the passed DataFrame
    v_data = df['voltage']
    c_data = df['current']

    v_data_ps, c_data_ps = filter_positive_values(v_data, c_data)
    v_data_ng, c_data_ng = filter_negative_values(v_data, c_data)

    # Step 2: Check for multiple sweeps
    num_sweeps = check_for_loops(v_data)

    # Step 3: Continue creating DataFrame with metrics
    metrics_df = create_device_dataframe(v_data, c_data, v_data_ps, c_data_ps, v_data_ng, c_data_ng)



    # Step 4: Handle single or multiple sweeps
    if num_sweeps > 1:
        _, _, df_file_stats = handle_multiple_sweeps(metrics_df, num_sweeps, device_path, None, plot_graph,
                                                     re_save_graph)
    else:
        _, _, df_file_stats = handle_single_sweep(metrics_df, None, device_path, plot_graph, re_save_graph)

    # Return both DataFrames (raw data_analyzer.py and metrics) for saving in main
    return df_file_stats, metrics_df

def file_analysis_endurance():
    print("endurance file")
    pass

def file_analysis_retention():
    print("retention file")
    pass


def create_device_dataframe(v_data, c_data, v_data_ps, c_data_ps, v_data_ng, c_data_ng):
    """ Create a DataFrame with voltage, current, and other metrics. """
    data = {
        'voltage': v_data,
        'current': c_data,
        'abs_current': absolute_val(c_data),
        'resistance': resistance(v_data, c_data),
        'voltage_ps': v_data_ps,
        'current_ps': c_data_ps,
        'voltage_ng': v_data_ng,
        'current_ng': c_data_ng,
        'log_Resistance': log_value(resistance(v_data, c_data)),
        'abs_Current_ps': absolute_val(c_data_ps),
        'abs_Current_ng': absolute_val(c_data_ng),
        'current_Density_ps': current_density_eq(v_data_ps, c_data_ps),
        'current_Density_ng': current_density_eq(v_data_ng, c_data_ng),
        'electric_field_ps': electric_field_eq(v_data_ps),
        'electric_field_ng': electric_field_eq(v_data_ng),
        'inverse_resistance_ps': inverse_resistance_eq(v_data_ps, c_data_ps),
        'inverse_resistance_ng': inverse_resistance_eq(v_data_ng, c_data_ng),
        'sqrt_Voltage_ps': sqrt_array(v_data_ps),
        'sqrt_Voltage_ng': sqrt_array(v_data_ng),
    }
    df = pd.DataFrame(data).dropna()
    return df


def split_loops(v_data, c_data, num_loops):
    """ Splits looped data_analyzer.py and outputs each sweep as another array """
    total_length = len(v_data)  # Assuming both v_data and c_data have the same length
    size = total_length // num_loops  # Calculate the size based on the number of loops

    # Convert size to integer
    size = int(size)

    # Handle the case when the division leaves a remainder
    if total_length % num_loops != 0:
        size += 1

    split_v_data = [v_data[i:i + size] for i in range(0, total_length, size)]
    split_c_data = [c_data[i:i + size] for i in range(0, total_length, size)]

    return split_v_data, split_c_data


def handle_multiple_sweeps(df, num_sweeps, device_path, file_info, plot_graph, re_save_graph):
    """ Handle logic for multiple sweeps """

    # Split loop data_analyzer.py
    split_v_data, split_c_data = split_loops(df['voltage'], df['current'], num_sweeps)

    # Calculate metrics for multiple sweeps
    ps_areas, ng_areas, areas, normalized_areas, ron, roff, von, voff = calculate_metrics_for_loops(split_v_data,
                                                                                                    split_c_data)

    # Store metrics in DataFrame
    file_stats = {
        'ps_area_avg': sum(ps_areas) / len(ps_areas),
        'ng_area_avg': sum(ng_areas) / len(ng_areas),
        'areas_avg': sum(areas) / len(areas),
        'normalized_areas_avg': sum(normalized_areas) / len(normalized_areas),
        'resistance_on_value': sum(ron) / len(ron),
        'resistance_off_value': sum(roff) / len(roff),
        'ON_OFF_Ratio': zero_devision_check(sum(ron) / len(ron), sum(roff) / len(roff)),
        'voltage_on_value': sum(von) / len(von),
        'voltage_off_value': sum(voff) / len(voff),
    }
    df_file_stats = pd.DataFrame([file_stats])

    # Plotting
    if plot_graph:
        # plot all
        plot_single_sweep_data(df, file_info, device_path, re_save_graph)
        # plot individual here
        plot_loop_data(split_v_data, split_c_data, file_info, device_path, re_save_graph)



    return file_stats, None, df_file_stats


def handle_single_sweep(df, file_info, device_path, plot_graph, re_save_graph):
    """ Handle logic for single sweep """

    # Calculate metrics for a single sweep
    ps_area, ng_area, area, normalized_area = area_under_curves(df['voltage'], df["current"])
    resistance_on_value, resistance_off_value, voltage_on_value, voltage_off_value = on_off_values(df['voltage'],
                                                                                                   df["current"])

    # Store metrics in DataFrame
    file_stats = {
        'ps_area': ps_area,
        'ng_area': ng_area,
        'area': area,
        'normalized_area': normalized_area,
        'resistance_on_value': resistance_on_value,
        'resistance_off_value': resistance_off_value,
        'ON_OFF_Ratio': zero_devision_check(resistance_on_value, resistance_off_value),
        'voltage_on_value': voltage_on_value,
        'voltage_off_value': voltage_off_value,
    }
    df_file_stats = pd.DataFrame([file_stats])

    # Plotting
    if plot_graph:
        plot_single_sweep_data(df, file_info, device_path, re_save_graph)

    return None, None, df_file_stats

#def read_file_to_dataframe(file):

    # try:
    #     df = pd.read_csv(file, sep='\s+', header=0)
    #     if 'voltage current' in df.columns:
    #         df[['voltage', 'current']] = df['voltage current'].str.split(expand=True)
    #         df.drop(columns=['voltage current'], inplace=True)
    #     return df
    # except Exception as e:
    #     print(f"Error reading file {file}: {e}")
    #     return None

def read_file_to_dataframe(file):
    try:
        df = pd.read_csv(file, sep='\s+', header=0)

        # Normalize column names to lowercase for consistency
        df.columns = [col.lower() for col in df.columns]

        # Find the column that contains 'voltage' and 'current'
        target_col = next((col for col in df.columns if 'voltage' in col and 'current' in col), None)

        if target_col:
            split_values = df[target_col].str.split(expand=True)

            if "time" in target_col:
                df[['voltage', 'current', 'time']] = split_values.iloc[:, :3]  # Extract first 3 columns
            else:
                df[['voltage', 'current']] = split_values.iloc[:, :2]  # Extract first 2 columns

            df.drop(columns=[target_col], inplace=True)  # Drop the original combined column

        # Ensure numeric dtypes for downstream computations
        for col in ['voltage', 'current', 'time']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows where voltage or current are NaN after conversion
        if 'voltage' in df.columns and 'current' in df.columns:
            df = df.dropna(subset=['voltage', 'current'])

        return df

    except Exception as e:
        print(f"Error reading file {file}: {e}")
        return None

def add_metadata(df, material, sample, section, device, filename):
    df['Material'] = material
    df['Sample'] = sample
    df['Section'] = section
    df['Device'] = device
    df['Filename'] = filename


# Analyze the file based on sweep type
def analyze_file(sweep_type, analysis_params):
    if sweep_type == 'Iv_sweep':
        return file_analysis(**analysis_params)
    elif sweep_type == 'Endurance':
        return file_analysis_endurance(**analysis_params)
    elif sweep_type == 'Retention':
        return file_analysis_retention(**analysis_params)
    else:
        return None, None


def save_to_hdf5(store_path, key_file_stats, key_raw_data, df_file_stats, df_raw_data):
    """Save metrics and raw dataframes into HDF5 at the given keys.

    If datasets already exist, they are overwritten.
    """
    if df_raw_data is None or df_file_stats is None:
        return

    structured_raw_data = dataframe_to_structured_array(df_raw_data)
    structured_file_stats = dataframe_to_structured_array(df_file_stats)

    if structured_raw_data is None or structured_file_stats is None:
        return

    with h5py.File(store_path, 'a') as f:
        if key_raw_data in f:
            del f[key_raw_data]
        f.create_dataset(key_raw_data, data=structured_raw_data, compression="gzip", dtype=structured_raw_data.dtype)

        if key_file_stats in f:
            del f[key_file_stats]
        f.create_dataset(key_file_stats, data=structured_file_stats, compression="gzip",
                         dtype=structured_file_stats.dtype)


# Save raw data_analyzer.py and metrics to HDF5
# def save_to_hdf5(store_path, key_raw, key_metrics, df_file_stats, df_raw_data):
#     # print("key_metrics" , key_metrics)
#     # print("key_raw",key_raw
#     # converet to structured array
#     structured_file_stats=dataframe_to_structured_array(df_file_stats)
#     structured_raw_data = dataframe_to_structured_array(df_raw_data)
#
#     with h5py.File("C:/temp/memristor_data2.h5", "w") as f:
#         f.create_dataset("raw_data", data_analyzer.py=structured_raw_data, compression="gzip")
#         f.create_dataset("file_stats", data_analyzer.py=structured_file_stats, compression="gzip")
#
#     # if df_file_stats is not None and not df_file_stats.empty:
#     #     store_path.put(key_raw, df_file_stats)
#     # if df_raw_data is not None and not df_raw_data.empty:
#     #     store_path.put(key_metrics, df_raw_data)