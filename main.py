import os.path

import pandas as pd
from pathlib import Path

import excell
from helpers import generate_analysis_params, extract_file_info, check_if_file_exists, print_progress, check_for_nan, \
    generate_hdf5_keys, check_sweep_type
from file_processing import read_file_to_dataframe, add_metadata, analyze_file, save_to_hdf5
from metrics_calculation import update_device_metrics_summary, write_device_summary
from tables import NaturalNameWarning
from excell import save_info_from_solution_devices_excell,save_info_from_device_into_excell
import warnings

# todo summary file needs chaging so its saved in level 4 not in the code level gpt was useless here

# what should the code do
calculate_raw = True  # All raw files
calculate_currated = False # Statistical analysis on curated files.

# Constants for configuration
FORCE_RECALCULATE = False  # Set to True to force recalculation and overwrite existing data in HDF5
PRINT_INTERVAL = 10  # Number of files after which progress is printed
OUTPUT_FILE = "skipped_files.txt"  # File to store skipped files or unknown sweep types
SUMMARY_FILE = "device_metrics_summary.txt"  # File to store the device-level summary
OUTPUT_FILE_Currated = "skipped_files_Currated.txt"  # File to store skipped files or unknown sweep types
SUMMARY_FILE_Currated = "device_metrics_summary_Currated.txt"  # File to store the device-level summary

# # # paths for test
# user_dir = Path.home()
# base_dir = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Memristors")
# base_currated = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Curated Data")

# paths
user_dir = Path.home()
base_dir = user_dir / Path("OneDrive - The University of Nottingham/Documents/Phd/2) Data/1) Devices/1) Memristors")
base_currated = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Curated Data")


warnings.filterwarnings('ignore', category=NaturalNameWarning)
skipped_files2 = []
skipped_files_currated = []


def process_files_raw(txt_files, base_dir, store):
    processed_files = 0
    current_sample = None
    device_metrics_summary = {}  # Track metrics for each device

    for i, file in enumerate(txt_files, 1):
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        if depth != 6:
            continue
        #print(relative_path)
        # Extract file information
        filename, device, section, sample, material, nano_particles = extract_file_info(relative_path)

        # Generate keys for HDF5 storage
        key_info, key_metrics = generate_hdf5_keys(material, sample, section, device, filename)

        # Check if the file exists in HDF5 and skip if necessary
        if not FORCE_RECALCULATE and check_if_file_exists(store, key_info):
            print(f"File {filename} already exists in HDF5. Skipping...")
            continue

        # Moving on to a new sample
        if sample != current_sample:
            current_sample = sample
            print(f"Moving on to new sample: {sample}")

        # Check if the sweep type is known
        sweep_type = check_sweep_type(file, OUTPUT_FILE)


        # Read the file and process it
        #  Check for nan values
        df = read_file_to_dataframe(file)
        if df is None or check_for_nan(df) or sweep_type is None:
            skipped_files2.append(file)
            continue

        add_metadata(df, material, sample, section, device, filename)

        # Generate the analysis parameters
        analysis_params = generate_analysis_params(df, filename, base_dir, device)

        # Analyze the file based on its sweep type

        df_file_stats, metrics_df = analyze_file(sweep_type, analysis_params)

        # pull the info from another sheet


        if metrics_df is not None:
            # finds the classification within the excell file and adds it to the end of the dataframe
            Sample_location = os.path.join(base_dir,nano_particles,material,sample)
            result = save_info_from_device_into_excell(sample, Sample_location)
            classification = excell.device_clasification(result,device,section,Sample_location)
            classification = classification
            metrics_df['classification'] = classification
        else:
            print("metrics_df is None, cannot assign classification.")
            print("check file,", key_info )

        # TODO do the same again for the quantum dot spacing as well from another excell document




        # Save raw data and metrics to HDF5
        save_to_hdf5(store, key_info, key_metrics, df_file_stats, metrics_df)

        # Update the device metrics summary with new metrics
        update_device_metrics_summary(device_metrics_summary, filename, device, section, sample, material, metrics_df)


        # todo add in yield to the document me
        # todo find whats in the updated metrics summary

        # Track progress and print it
        processed_files += 1
        print_progress(processed_files, len(txt_files), PRINT_INTERVAL)

    # Write the device-level summary after all files are processed
    # this currently saves at the location of the code!!
    write_device_summary(device_metrics_summary, SUMMARY_FILE)

    misssing_number = len(txt_files) - processed_files

    print(
        f"Processing complete: {processed_files}/{len(txt_files)} files processed, with {misssing_number} files missing:")
    print(" ")
    for file in skipped_files2:
        print(file)

def process_files_currated(txt_files, base_dir, store):
    processed_files = 0
    current_sample = None
    device_metrics_summary = {}  # Track metrics for each device

    print("working on currated data")

    # is there a way too take all the currated data and pull it from the h5 file
    # currate data is displayed as follows in files
    # name_in_checked_files = f"{self.material} - {self.polymer} - {self.sample_name} - {self.section_folder} - {self.device_folder} - {self.filename}"
    # with folder structure like this
    # output_folder2 = os.path.join(self.output_folder, self.material, self.polymer, self.sample_name

    for i, file in enumerate(txt_files, 1):
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        if depth != 6:
            continue


        # Extract file information this needs changing to extract the relavent information
        filename, device, section, sample, material = extract_file_info(relative_path)

        # Generate keys for HDF5_curated storage, again names need changing or checking. keep it the same format as normal
        key_raw, key_metrics = generate_hdf5_keys(material, sample, section, device, filename)

        # Check if the file exists in HDF5 and skip if necessary
        if not FORCE_RECALCULATE and check_if_file_exists(store, key_raw):
            print(f"File {filename} already exists in HDF5. Skipping...")
            continue

        # Moving on to a new sample
        if sample != current_sample:
            current_sample = sample
            print(f"Moving on to new sample: {sample}")

        # Read the file and process it
        #  Check for nan values
        df = read_file_to_dataframe(file)
        if df is None or check_for_nan(df):
            skipped_files_currated.append(file)
            continue

        add_metadata(df, material, sample, section, device, filename)

        # Generate the analysis parameters
        analysis_params = generate_analysis_params(df, filename, base_dir, device)


        # Analyze the file based on its sweep type
        sweep_type = check_sweep_type(file, OUTPUT_FILE_Currated)

        df_file_stats, metrics_df = analyze_file(sweep_type, analysis_params)

        # look at excell file here
        # check the file and load it in before doing the bellow passing the dataframe to it
        #save_info_from_solution_devices_excell(device_name, excel_path)
        # append the classification given to the end of the dataframe for the device

        # Save raw data and metrics to HDF5
        save_to_hdf5(store, key_raw, key_metrics, df_file_stats, metrics_df)
        print(key_raw)

        # Update the device metrics summary with new metrics
        update_device_metrics_summary(device_metrics_summary, filename, device, section, sample, material, metrics_df)

        # Track progress and print it
        processed_files += 1
        print_progress(processed_files, len(txt_files), PRINT_INTERVAL)

    # Write the device-level summary after all files are processed
    write_device_summary(device_metrics_summary, SUMMARY_FILE_Currated)

    misssing_number = len(txt_files) - processed_files

    print(
        f"Processing complete: {processed_files}/{len(txt_files)} files processed, with {misssing_number} files missing:")
    print("")
    for file in skipped_files_currated:
        print(file)

# Extract file info (at depth 6)
def extract_file_info(relative_path):
    filename = relative_path.parts[-1]  # Depth 6 -> Filename
    device = relative_path.parts[4]  # Depth 5 -> Device
    section = relative_path.parts[3]  # Depth 4 -> Section
    sample = relative_path.parts[2]  # Depth 3 -> Sample
    material = relative_path.parts[1]  # Depth 2 -> Material
    nanoparticles = relative_path.parts[0]
    return filename, device, section, sample, material,nanoparticles


def main(base_dir,base_currated,calculate_raw,calculate_currated):
    # Set the working directory to the user's home directory'

    txt_files_base = list(f for f in base_dir.rglob('*.txt') if len(f.relative_to(base_dir).parts) == 6)
    txt_files_curr = list(f for f in base_currated.rglob('*.txt') if len(f.relative_to(base_currated).parts) == 6)

    if calculate_raw:
        # Process all raw files
        with pd.HDFStore('memristor_data.h5') as store:
            process_files_raw(txt_files_base, base_dir, store)

    if calculate_currated:
        # process currated files
        with pd.HDFStore('Currated__data.h5') as store:
            process_files_currated(txt_files_curr, base_currated, store)


if __name__ == '__main__':
    main(base_dir,base_currated,calculate_raw,calculate_currated)
