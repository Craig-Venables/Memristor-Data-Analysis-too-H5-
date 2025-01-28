import os
import shutil
import time
import pickle
import pandas as pd

""" Any interacting with Excell goes here"""
# add in other sheet

def save_info_from_solution_devices_excell(device_name, excel_path):
    '''
    Takes the device name looks up the information within the excel document given and returns all the information
    on the device and the solutions used for the different solutions.
    saves it as a text document for easy reading and as a pkl file for python.
    :param device_name: Device Name
    :param excel_path: Path to the Excel file "solutions and devices"
    :param foldername:
    :return: Saves device parameters as a data frame
    '''
    try:
        # Read the Excel file into a DataFrame without modifying it
        with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
            df = pd.read_excel(xls, sheet_name='Memristor Devices')

        # Find the row with the given device name in the "Device Full Name" column
        row = df[df['Device Full Name'] == device_name]

        if not row.empty:
            # Extract information from the found row
            info_dict = {
                'Device Full Name': row.iloc[0]['Device Full Name'],
                'B-Electrode (nm)': row.iloc[0]['B-Electrode (nm)'],
                'B-Material': row.iloc[0]['B-Material'],
                'Solution 1 ID': row.iloc[0]['Solution 1 ID'],
                'Solution 1 Spin Speed': row.iloc[0]['Solution 1 Spin Speed'],
                'Solution 2 ID': row.iloc[0]['Solution 2 ID'],
                'Solution 2 Spin Speed': row.iloc[0]['Solution 2 Spin Speed'],
                'Solution 3 ID': row.iloc[0]['Solution 3 ID'],
                'Solution 3 Spin Speed': row.iloc[0]['Solution 3 Spin Speed'],
                'Solution 4 ID': row.iloc[0]['Solution 4 ID'],
                'Solution 4 Spin Speed': row.iloc[0]['Solution 4 Spin Speed'],
                'T-Electrode (nm)': row.iloc[0]['T-Electrode (nm)'],
                'T-Material': row.iloc[0]['T-Material'],
                '# Barrier': row.iloc[0]['# Barrier'],
                'Layer 1': row.iloc[0]['Layer 1'],
                'Layer 2': row.iloc[0]['Layer 2'],
                'Layer 3': row.iloc[0]['Layer 3'],
                'Layer 4': row.iloc[0]['Layer 4'],
                'Np Type': row.iloc[0]['Np Type'],
                'Np Concentraion': row.iloc[0]['Np Concentraion'], # this is spelt wrong
                'Oz Clean Time': row.iloc[0]['Oz Clean Time'],
                'Np Solution Id': row.iloc[0]['Np Solution Id'],
                'Np Material': row.iloc[0]['Np Material'],
                'Polymer': row.iloc[0]['Polymer'],
                # Add more fields as needed
            }
            #print(info_dict)

            solutions = ["Solution 1 ID", "Solution 2 ID", "Solution 3 ID", "Solution 4 ID"]

            # Read the Excel file into a DataFrame without modifying it
            with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
                df = pd.read_excel(xls, sheet_name='Prepared Solutions')

            # Loop through solutions
            for solution in solutions:
                df_solutions = df[df['Solution Id'] == info_dict.get(solution)]

                if pd.notnull(info_dict.get(solution)):
                    if not df_solutions.empty:
                        # extract information about solutions
                        info_dict['Solution #'+ solution] = df_solutions.iloc[0]['Solution #']
                        info_dict['Np Solution used ' + solution] = df_solutions.iloc[0]['Np Solution used']
                        info_dict['Polymer 1 ' + solution] = df_solutions.iloc[0]['Polymer 1']
                        info_dict['Polymer 2 ' + solution] = df_solutions.iloc[0]['Polymer 2']
                        info_dict['Polymer % ' + solution] = df_solutions.iloc[0]['Polymer %']
                        info_dict['Np solution mg/ml ' + solution] = df_solutions.iloc[0]['Np solution mg/ml']
                        info_dict['Np Stock Solution Weight ' + solution] = df_solutions.iloc[0]['Np Stock Solution Weight']
                        info_dict['Polymer 1 Weight ' + solution] = df_solutions.iloc[0]['Polymer 1 Weight']
                        info_dict['Polymer 2 Weight ' + solution] = df_solutions.iloc[0]['Polymer 2 Weight']
                        info_dict['Solvent Weight ' + solution] = df_solutions.iloc[0]['Solvent Weight']
                        info_dict['Actual polymer (%) ' + solution] = df_solutions.iloc[0]['Actual polymer (%)']
                        info_dict['Polymer ratio % ' + solution] = df_solutions.iloc[0]['Polymer ratio %']
                        info_dict['Solvent ' + solution] = df_solutions.iloc[0]['Solvent ']  # this has a space at end
                        info_dict['Controll? ' + solution] = df_solutions.iloc[0]['Controll?']
                        info_dict['Np Type ' + solution] = df_solutions.iloc[0]['Np Type']
                        info_dict['Calculated mg/ml ' + solution] = df_solutions.iloc[0]['Calculated mg/ml']
                        info_dict['Polymer Density ' + solution] = df_solutions.iloc[0]['Polymer Density']
                        info_dict['Solvent Density ' + solution] = df_solutions.iloc[0]['Solvent Density']
                        info_dict['Np Material ' + solution] = df_solutions.iloc[0]['Np Material']
                        info_dict['Mg of Quantum dots used ' + solution] = df_solutions.iloc[0]['Mg of Quantum dots used']
                        info_dict['Stock Np Solution Concentration ' + solution] = df_solutions.iloc[0]['Stock Np Solution Concentration']
                    else:
                        print(f"Skipping search in 'Prepared Solutions' because Solution {solution} ID is blank or null.")
                        continue  # Skip the rest of the loop for this solution ID

            # # Save the dictionary to a file using pickle
            # with open(savelocation +'/Device_fabrication_info_dict.pkl', 'wb') as file:
            #     pickle.dump(info_dict, file)
            #
            # # Save information to a text file for easy reading
            # with open(savelocation +'/Device_fabrication_info.txt', 'w') as txt_file:
            #     txt_file.write("Information for device '{}':\n".format(device_name))
            #     for key, value in info_dict.items():
            #         txt_file.write(f"{key}: {value}\n")
            # #print("saved", device_name,"information" )

            #info_dict_df = pd.DataFrame.from_dict(info_dict)

            return (info_dict)

        else:
            print(f"Error: Device '{device_name}' not found in Excel file.")

    except Exception as e:
        print(f"Error: {str(e)}")


def save_info_from_device_into_excell(device_name,device_fol_location):
    '''
    Takes the device name looks up the information within the excel document for device swweeps given and returns all the information
    on the device and the solutions used for the different solutions.
    saves it as a text document for easy reading and as a pkl file for python.
    :param device_name: Device Name

    :return: Saves device parameters as a data frame
    '''
    excel_path = device_fol_location +"\\"+ device_name + ".xlsx"
    #print(excel_path)

    try:
        # Read the Excel file into a DataFrame without modifying it
        with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
            df = pd.read_excel(xls, sheet_name='Sheet1')

            # List to store DataFrames for each section
            section_dataframes = {}

            # Loop through sections from 'A' to 'L'
            for section in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
                section_data = df[df['Section '] == section]
                if not section_data.empty:
                    section_dataframes[section] = section_data
            # print(section_dataframes['G'])
            #print(section_dataframes['G'])
            return section_dataframes

    except Exception as e:
        print(f"Error: {str(e)}")


def update_and_save_to_excel(device_name, device_fol_location, section_to_update, new_data):
    '''
    Takes the device name, looks up the information within the Excel document for device sweeps given,
    updates the specified section with new data, and saves it back to the Excel sheet.

    :param device_name: Device Name
    :param device_fol_location: Folder location for the Excel file
    :param section_to_update: Section to update (e.g., 'G')
    :param new_data: New data to replace the existing data in the specified section

    :return: None
    '''

    excel_path = os.path.join(device_fol_location, f"{device_name}.xlsx")

    try:
        # Read the Excel file into a DataFrame
        with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
            df = pd.read_excel(xls, sheet_name='Sheet1')

            # Update the specified section with new data
            section_data = df[df['Section '] == section_to_update]
            if not section_data.empty:
                df.loc[df['Section '] == section_to_update] = new_data

                # Save the updated DataFrame back to Excel
                df.to_excel(excel_path, sheet_name='Sheet1', index=False)
                print("Updated")

    except Exception as e:
        print(f"Error: {str(e)}")


def device_clasification(excell_dict, device_folder, section_folder, path):
    """ extracts the classification from the device_number excel sheet for the device level """
    try:
        section_folder = section_folder[0].upper()
        # Take only the first letter from the section_folder
        # Take only the first two digits from the device_folder
        device_folder = device_folder[:2]

        # print(device_folder)
        #print(excell_dict[section_folder])
        df = excell_dict[section_folder]
        # Convert device_folder to the same type as in the DataFrame (assuming it's numeric)
        device_folder = int(device_folder)
        # Find the row where the "Device #" matches the specified device_folder
        result_row = df[df["Device #"] == device_folder]
        # Extract the classification value
        classification = result_row["Classification"].values[
            0] if not result_row.empty else None
        # print(classification)
        return (classification)
    except:
        print("please add xls too ", path)
        return None