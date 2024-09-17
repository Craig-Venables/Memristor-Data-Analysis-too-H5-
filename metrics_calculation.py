import numpy as np
import math
import os
from helpers import bounds
import re
import pandas as pd

def calculate_metrics_for_loops(split_v_data, split_c_data):
    '''
    Calculate various metrics for each split array of voltage and current data.
    anything that needs completing on loops added in here

    Parameters:
    - split_v_data (list of lists): List containing split voltage arrays
    - split_c_data (list of lists): List containing split current arrays

    Returns:
    - ps_areas (list): List of PS areas for each split array
    - ng_areas (list): List of NG areas for each split array
    - areas (list): List of total areas for each split array
    - normalized_areas (list): List of normalized areas for each split array
    '''

    # Initialize lists to store the values for each metric
    ps_areas = []
    ng_areas = []
    areas = []
    normalized_areas = []
    ron = []
    roff = []
    von = []
    voff = []

    # Loop through each split array
    for idx in range(len(split_v_data)):
        sub_v_array = split_v_data[idx]
        sub_c_array = split_c_data[idx]

        #print(sub_v_array)

        # Call the area_under_curves function for the current split arrays
        ps_area, ng_area, area, norm_area = area_under_curves(sub_v_array, sub_c_array)

        # Append the values to their respective lists
        ps_areas.append(ps_area)
        ng_areas.append(ng_area)
        areas.append(area)
        normalized_areas.append(norm_area)

        r_on, r_off, v_on, v_off = on_off_values(sub_v_array, sub_c_array)

        ron.append(r_on)
        roff.append(r_off)
        von.append(v_on)
        voff.append(v_off)

        # Print the values for the current split array
        # print(f"Metrics for split array {idx + 1}:")
        # print(f"PS Area Enclosed: {ps_area}")
        # print(f"NG Area Enclosed: {ng_area}")
        # print(f"Total Area Enclosed: {area}")
        # print(f"Normalized Area Enclosed: {norm_area}")
        # print("------")

    # Print the lists of values
    # print("\nList of PS Areas:", ps_areas)
    # print("List of NG Areas:", ng_areas)
    # print("List of Total Areas:", areas)
    # print("List of Normalized Areas:", normalized_areas)

    # Return the calculated metrics
    return ps_areas, ng_areas, areas, normalized_areas, ron, roff, von, voff

def area_under_curves(v_data, c_data):
    """
    only run this for an individual sweep
    :return: ps_area_enclosed,ng_area_enclosed,total_area_enclosed
    """
    # finds v max and min
    v_max, v_min = bounds(v_data)

    # creates dataframe of the sweep in sections
    df_sections = split_data_in_sect(v_data, c_data, v_max, v_min)

    # calculate the area under the curve for each section
    sect1_area = abs(area_under_curve(df_sections.get('voltage_ps_sect1'), df_sections.get('current_ps_sect1')))
    sect2_area = abs(area_under_curve(df_sections.get('voltage_ps_sect2'), df_sections.get('current_ps_sect2')))
    sect3_area = abs(area_under_curve(df_sections.get('voltage_ng_sect1'), df_sections.get('current_ng_sect1')))
    sect4_area = abs(area_under_curve(df_sections.get('voltage_ng_sect2'), df_sections.get('current_ng_sect2')))

    # plot to show where each section is on the hysteresis
    # plt.plot(df_sections.get('voltage_ps_sect1'), df_sections.get('current_ps_sect1'),color="blue" )
    # plt.plot(df_sections.get('voltage_ps_sect2'), df_sections.get('current_ps_sect2'),color="green")
    # plt.plot(df_sections.get('voltage_ng_sect1'), df_sections.get('current_ng_sect1'),color="red")
    # plt.plot(df_sections.get('voltage_ng_sect2'), df_sections.get('current_ng_sect2'),color="yellow")
    # #plt.legend()
    # plt.show()
    # plt.pause(0.1)

    # blue - green
    # red - yellow

    ps_area_enclosed = abs(sect1_area) - abs(sect2_area)
    ng_area_enclosed = abs(sect4_area) - abs(sect3_area)
    area_enclosed = ps_area_enclosed + ng_area_enclosed
    norm_area_enclosed = area_enclosed / (abs(v_max) + abs(v_min))

    # added nan check as causes issues later if not a value
    if math.isnan(norm_area_enclosed):
        norm_area_enclosed = 0
    if math.isnan(ps_area_enclosed):
        ps_area_enclosed = 0
    if math.isnan(ng_area_enclosed):
        ng_area_enclosed = 0
    if math.isnan(area_enclosed):
        area_enclosed = 0

    return ps_area_enclosed, ng_area_enclosed, area_enclosed, norm_area_enclosed

def on_off_values(voltage_data, current_data):
    """
    Calculates r on off and v on off values for an individual device
    """
    # Convert DataFrame columns to lists
    voltage_data = voltage_data.to_numpy()
    current_data = current_data.to_numpy()
    # Initialize lists to store Ron and Roff values
    resistance_on_value = []
    resistance_off_value = []
    # Initialize default values for on and off voltages
    voltage_on_value = 0
    voltage_off_value = 0

    # Get the maximum voltage value
    max_voltage = round(max(voltage_data), 1)
    # Catch edge case for just negative sweep only
    if max_voltage == 0:
        max_voltage = abs(round(min(voltage_data), 1))

    # Set the threshold value to 0.2 times the maximum voltage
    threshold = round(0.2 * max_voltage, 2)
    # print("threshold,max_voltage")
    # print(threshold,max_voltage)
    # print(len(voltage_data))
    # print(voltage_data)

    # Filter the voltage and current data to include values within the threshold
    filtered_voltage = []
    filtered_current = []
    for index in range(len(voltage_data)):
        #print(index)
        if -threshold < voltage_data[index] < threshold:
            filtered_voltage.append(voltage_data[index])
            filtered_current.append(current_data[index])
    # print(filtered_voltage)

    resistance_magnitudes = []
    for idx in range(len(filtered_voltage)):
        if filtered_voltage[idx] != 0 and filtered_current[idx] != 0:
            resistance_magnitudes.append(abs(filtered_voltage[idx] / filtered_current[idx]))

    if not resistance_magnitudes:
        # Handle the case when the list is empty, e.g., set default values or raise an exception.
        print("Error: No valid resistance values found.")
        return 0, 0, 0, 0

    # # Calculate the resistance magnitude for each filtered data point
    # resistance_magnitudes = []
    # for idx in range(len(filtered_voltage)):
    #     if filtered_voltage[idx] != 0:
    #         resistance_magnitudes.append(abs(filtered_voltage[idx] / filtered_current[idx]))
    # print(resistance_magnitudes)
    # Store the minimum and maximum resistance values
    resistance_off_value = min(resistance_magnitudes)
    resistance_on_value = max(resistance_magnitudes)

    # Calculate the gradients for each data point
    gradients = []
    for idx in range(len(voltage_data)):
        if idx != len(voltage_data) - 1:
            if voltage_data[idx + 1] - voltage_data[idx] != 0:
                gradients.append(
                    (current_data[idx + 1] - current_data[idx]) / (voltage_data[idx + 1] - voltage_data[idx]))

    # Find the maximum and minimum gradient values
    max_gradient = max(gradients[:(int(len(gradients) / 2))])
    min_gradient = min(gradients)

    # Use the maximum and minimum gradient values to determine the on and off voltages
    for idx in range(len(gradients)):
        if gradients[idx] == max_gradient:
            voltage_off_value = voltage_data[idx]
        if gradients[idx] == min_gradient:
            voltage_on_value = voltage_data[idx]

    # Return the calculated Ron and Roff values and on and off voltages
    return resistance_on_value, resistance_off_value, voltage_on_value, voltage_off_value

def split_data_in_sect(voltage, current, v_max, v_min):
    # splits the data into sections and clculates the area under the curve for how "memeristive" a device is.
    zipped_data = list(zip(voltage, current))

    positive = [(v, c) for v, c in zipped_data if 0 <= v <= v_max]
    negative = [(v, c) for v, c in zipped_data if v_min <= v <= 0]

    # Find the maximum length among the four sections
    max_len = max(len(positive), len(negative))

    # Split positive section into two equal parts
    positive1 = positive[:max_len // 2]
    positive2 = positive[max_len // 2:]

    # Split negative section into two equal parts
    negative3 = negative[:max_len // 2]
    negative4 = negative[max_len // 2:]

    # Find the maximum length among the four sections
    max_len = max(len(positive1), len(positive2), len(negative3), len(negative4))

    # Calculate the required padding for each section
    pad_positive1 = max_len - len(positive1)
    pad_positive2 = max_len - len(positive2)
    pad_negative3 = max_len - len(negative3)
    pad_negative4 = max_len - len(negative4)

    # Limit the padding to the length of the last value for each section
    last_positive1 = positive1[-1] if positive1 else (0, 0)
    last_positive2 = positive2[-1] if positive2 else (0, 0)
    last_negative3 = negative3[-1] if negative3 else (0, 0)
    last_negative4 = negative4[-1] if negative4 else (0, 0)

    positive1 += [last_positive1] * pad_positive1
    positive2 += [last_positive2] * pad_positive2
    negative3 += [last_negative3] * pad_negative3
    negative4 += [last_negative4] * pad_negative4

    # Create DataFrame for device
    sections = {
        'voltage_ps_sect1': [v for v, _ in positive1],
        'current_ps_sect1': [c for _, c in positive1],
        'voltage_ps_sect2': [v for v, _ in positive2],
        'current_ps_sect2': [c for _, c in positive2],
        'voltage_ng_sect1': [v for v, _ in negative3],
        'current_ng_sect1': [c for _, c in negative3],
        'voltage_ng_sect2': [v for v, _ in negative4],
        'current_ng_sect2': [c for _, c in negative4],
    }

    df_sections = pd.DataFrame(sections)
    return df_sections

def area_under_curve(voltage, current):
    """
    Calculate the area under the curve given voltage and current data.
    """

    # print(voltage,current)
    voltage = np.array(voltage)
    current = np.array(current)
    # Calculate the area under the curve using the trapezoidal rule
    area = np.trapz(current, voltage)
    # which ever is in np.trapz(y,x), Using a decreasing x corresponds to integrating in reverse: ie negative value?
    return area
