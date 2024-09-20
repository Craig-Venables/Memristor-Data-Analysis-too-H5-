import pandas as pd
from pathlib import Path
from helpers import generate_analysis_params, extract_file_info, check_if_file_exists, print_progress,check_for_nan,generate_hdf5_keys,check_sweep_type
from file_processing import read_file_to_dataframe, add_metadata, analyze_file, save_to_hdf5
from metrics_calculation import update_device_metrics_summary, write_device_summary
from tables import NaturalNameWarning
import warnings

#todo summary file needs chaging so its saved in level 4 not in the code level gpt was useless here

# Constants for configuration
FORCE_RECALCULATE = True  # Set to True to force recalculation and overwrite existing data in HDF5
PRINT_INTERVAL = 50  # Number of files after which progress is printed
OUTPUT_FILE = "skipped_files.txt"  # File to store skipped files or unknown sweep types
SUMMARY_FILE = "device_metrics_summary.txt"  # File to store the device-level summary

warnings.filterwarnings('ignore', category=NaturalNameWarning)

def process_files(txt_files, base_dir, store):
    processed_files = 0
    current_sample = None
    device_metrics_summary = {}  # Track metrics for each device

    for i, file in enumerate(txt_files, 1):
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        if depth != 6:
            continue

        # Extract file information
        filename, device, section, sample, material = extract_file_info(relative_path)

        # Generate keys for HDF5 storage
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
        df = read_file_to_dataframe(file)
        if df is None or check_for_nan(df):
            continue

        add_metadata(df, material, sample, section, device, filename)

        # Generate the analysis parameters
        analysis_params = generate_analysis_params(df, filename, base_dir, device)

        # Analyze the file based on its sweep type
        sweep_type = check_sweep_type(file, OUTPUT_FILE)
        df_file_stats, metrics_df = analyze_file(sweep_type, analysis_params)

        # Save raw data and metrics to HDF5
        save_to_hdf5(store, key_raw, key_metrics, df_file_stats, metrics_df)

        # Update the device metrics summary with new metrics
        update_device_metrics_summary(device_metrics_summary, filename, device, section, sample, material, metrics_df)

        # Track progress and print it
        processed_files += 1
        print_progress(processed_files, len(txt_files), PRINT_INTERVAL)

    # Write the device-level summary after all files are processed
    write_device_summary(device_metrics_summary, SUMMARY_FILE)
    print(f"Processing complete: {processed_files}/{len(txt_files)} files processed.")

# Extract file info (at depth 6)
def extract_file_info(relative_path):
    filename = relative_path.parts[-1]  # Depth 6 -> Filename
    device = relative_path.parts[4]     # Depth 5 -> Device
    section = relative_path.parts[3]    # Depth 4 -> Section
    sample = relative_path.parts[2]     # Depth 3 -> Sample
    material = relative_path.parts[1]   # Depth 2 -> Material
    return filename, device, section, sample, material

def main():
    user_dir = Path.home()
    base_dir = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Memristors")
    txt_files = list(f for f in base_dir.rglob('*.txt') if len(f.relative_to(base_dir).parts) == 6)

    with pd.HDFStore('memristor_data.h5') as store:
        process_files(txt_files, base_dir, store)

if __name__ == '__main__':
    main()