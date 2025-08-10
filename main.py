import os.path
from pathlib import Path
from datetime import datetime
import excell
from helpers import generate_analysis_params, check_if_file_exists, print_progress, check_for_nan, \
    generate_hdf5_keys, check_sweep_type
from file_processing import read_file_to_dataframe, add_metadata, analyze_file, save_to_hdf5
from metrics_calculation import update_device_metrics_summary, write_device_summary
try:
    from tables import NaturalNameWarning
except Exception:  # pragma: no cover - optional dependency
    class NaturalNameWarning(Warning):
        pass
from excell import save_info_from_solution_devices_excell, save_info_from_device_into_excell
import warnings

# Entry script to process raw or curated text files into HDF5 datasets

# what should the code do
calculate_raw = True  # All raw files
calculate_curated = False  # Statistical analysis on curated files.
# Toggle plotting of figures during processing (saves .png per file)
PLOT_GRAPHS = False

# Constants for configuration
FORCE_RECALCULATE = True  # Set to True to force recalculation and overwrite existing data in HDF5
PRINT_INTERVAL = 10  # Number of files after which progress is printed
OUTPUT_FILE = "skipped_files.txt"  # File to store skipped files or unknown sweep types
SUMMARY_FILE = "device_metrics_summary.txt"  # File to store the device-level summary
OUTPUT_FILE_CURATED = "skipped_files_curated.txt"  # File to store skipped curated files
SUMMARY_FILE_CURATED = "device_metrics_summary_curated.txt"  # File to store the curated device-level summary

debugging = False
user_dir = Path.home()

if debugging:
    # # paths for test
    base_dir = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Memristors")
    base_curated = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Curated Data")

else:
    # paths
    base_dir = user_dir / Path("OneDrive - The University of Nottingham/Documents/Phd/2) Data/1) Devices/1) Memristors")
    base_curated = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Curated Data")


# where do you want to save the h5 files?
save_location = user_dir / Path("OneDrive - The University of Nottingham\Documents\Phd\2) Data\1) Devices\1) Memristors")
# location of excell
solution_devices_excell_path = user_dir / Path("OneDrive - The University of Nottingham/Documents/Phd/solutions and devices.xlsx")

warnings.filterwarnings('ignore', category=NaturalNameWarning)
skipped_files2 = []
skipped_files_curated = []

def process_files_raw(txt_files, base_dir, store_path):
    processed_files = 0
    current_sample = None
    device_file_stats_summary = {}  # Track metrics for each device
    device_file_counts = {}  # Dictionary to store_path file counts per device

    for i, file in enumerate(txt_files, 1):
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        if depth != 6:
            continue
        #print(file, i)
        #print(relative_path)
        # Extract file information
        filename, device, section, sample, material, nano_particles = extract_file_info_with_nanoparticles(relative_path)

        # Generate keys for HDF5 storage, returns as _info and _metrics
        key_file_stats, key_raw_data = generate_hdf5_keys(material, sample, section, device, filename)

        # Check if the file exists in HDF5 and skip if necessary
        if not FORCE_RECALCULATE and check_if_file_exists(store_path, key_file_stats):
            print(f"File {filename} already exists in HDF5. Skipping...")
            continue

        # Moving on to a new sample
        if sample != current_sample:
            current_sample = sample
            print(f"Moving on to new sample: {sample}")
            device_fab_info = save_info_from_solution_devices_excell(sample, solution_devices_excell_path)
            device_fab_key = f'/{material}/{sample}_fabrication'

            # calculate yield here
            key_device_yield = f'/{material}/{sample}_yield'
            #df_yield =
        if device == 'plots_combined':
            continue

        # Check if the sweep type is known and/or if the file is a dud
        # returns 'iv_sweep' or None
        sweep_type = check_sweep_type(file, OUTPUT_FILE)

        #  Check for nan values and if so skip
        df = read_file_to_dataframe(file)
        if df is None or check_for_nan(df) or sweep_type is None:
            skipped_files2.append(file)
            continue

        # adds all the file metadata too df
        add_metadata(df, material, sample, section, device, filename)

        # Generate the analysis parameters for this script
        analysis_params = generate_analysis_params(df, filename, base_dir, device)

        # Respect plotting preference
        analysis_params['plot_graph'] = PLOT_GRAPHS
        # Analyze the file based on its sweep type returning two dataframes
        df_file_stats, df_raw_data = analyze_file(sweep_type, analysis_params)
        # metrics_df is all the data_analyzer.py I,V,R etc...
        # df_file_stats is the info on the sweep ie on off value etc...

        # Track the number of files per device
        device_key = (material, sample, section, device)  # Identify each unique device
        if device_key not in device_file_counts:
            device_file_counts[device_key] = 0
        device_file_counts[device_key] += 1  # Increment file count for this device


        # pull the info from the device finding the classification
        if df_raw_data is not None:
            # finds the classification within the excell file and adds it to the end of the dataframe
            Sample_location = os.path.join(base_dir, nano_particles, material, sample)
            result = save_info_from_device_into_excell(sample, Sample_location)
            classification = excell.device_clasification(result, device, section, Sample_location)
            classification = classification
            df_raw_data['classification'] = classification
        else:
            print("metrics_df is None, cannot assign classification.")
            print("check file,", key_file_stats )

        # TODO do the same again for the quantum dot spacing as well from another excell document
        key_df_sample_information = []
        df_sample_information = []

        # # Update device_file_stats_summary
        #update_device_metrics_summary(device_file_stats_summary, filename, device, section, sample, material, df_file_stats)

        # Save raw data_analyzer.py and metrics to HDF5
        # key_file_stats and key_metircs are the keys for the dataframes
        save_to_hdf5(store_path, key_file_stats, key_raw_data, df_file_stats, df_raw_data)

        # todo add in yield to the document me
        # todo find whats in the updated metrics summary
        #print("a")
        #print(list(device_file_stats_summary["1"]))
        #print(device_file_stats_summary)
        # Track progress and print it
        processed_files += 1
        print_progress(processed_files, len(txt_files), PRINT_INTERVAL)

    # Write the device-level summary after all files are processed
    # this currently saves at the location of the code!!
    #write_device_summary(device_file_stats_summary, SUMMARY_FILE)

    misssing_number = len(txt_files) - processed_files



    print(
        f"Processing complete: {processed_files}/{len(txt_files)} files processed, with {misssing_number} files missing:")
    print(" ")
    for file in skipped_files2:
        print(file)

def process_files_curated(txt_files, base_dir, store_path):
    processed_files = 0
    current_sample = None
    device_metrics_summary = {}  # Track metrics for each device

    print("working on curated data")

    # is there a way too take all the currated data_analyzer.py and pull it from the h5 file
    # currate data_analyzer.py is displayed as follows in files
    # name_in_checked_files = f"{self.material} - {self.polymer} - {self.sample_name} - {self.section_folder} - {self.device_folder} - {self.filename}"
    # with folder structure like this
    # output_folder2 = os.path.join(self.output_folder, self.material, self.polymer, self.sample_name

    for i, file in enumerate(txt_files, 1):
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        if depth != 6:
            continue


        # Extract file information
        filename, device, section, sample, material, _ = extract_file_info_with_nanoparticles(relative_path)

        # Generate keys for HDF5 storage
        key_file_stats, key_raw_data = generate_hdf5_keys(material, sample, section, device, filename)

        # Check if the file exists in HDF5 and skip if necessary
        if not FORCE_RECALCULATE and check_if_file_exists(store_path, key_file_stats):
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
            skipped_files_curated.append(file)
            continue

        add_metadata(df, material, sample, section, device, filename)

        # Generate the analysis parameters
        analysis_params = generate_analysis_params(df, filename, base_dir, device)
        analysis_params['plot_graph'] = PLOT_GRAPHS


        # Analyze the file based on its sweep type
        sweep_type = check_sweep_type(file, OUTPUT_FILE_CURATED)

        df_file_stats, metrics_df = analyze_file(sweep_type, analysis_params)

        # look at excell file here
        # check the file and load it in before doing the bellow passing the dataframe to it
        #save_info_from_solution_devices_excell(device_name, excel_path)
        # append the classification given to the end of the dataframe for the device

        # Save dataframes to HDF5
        save_to_hdf5(store_path, key_file_stats, key_raw_data, df_file_stats, metrics_df)
        #print(key_raw)

        # Update the device metrics summary with new metrics
        update_device_metrics_summary(device_metrics_summary, filename, device, section, sample, material, metrics_df)

        # Track progress and print it
        processed_files += 1
        print_progress(processed_files, len(txt_files), PRINT_INTERVAL)

    # Write the device-level summary after all files are processed
    write_device_summary(device_metrics_summary, SUMMARY_FILE_CURATED)

    misssing_number = len(txt_files) - processed_files

    print(
        f"Processing complete: {processed_files}/{len(txt_files)} files processed, with {misssing_number} files missing:")
    print("")
    for file in skipped_files_curated:
        print(file)

# Extract file info (expects depth 6): returns filename, device, section, sample, material, nanoparticles
def extract_file_info_with_nanoparticles(relative_path: Path):
    filename = relative_path.parts[-1]
    device = relative_path.parts[4]
    section = relative_path.parts[3]
    sample = relative_path.parts[2]
    material = relative_path.parts[1]
    nanoparticles = relative_path.parts[0]
    return filename, device, section, sample, material, nanoparticles


def main(base_dir, base_curated, calculate_raw, calculate_curated, save_location):
    # Discover files at expected depth
    txt_files_base = [f for f in base_dir.rglob('*.txt') if len(f.relative_to(base_dir).parts) == 6]
    txt_files_curated = [f for f in base_curated.rglob('*.txt') if len(f.relative_to(base_curated).parts) == 6]

    timestamp = datetime.now().strftime('%Y%m%d')

    if calculate_raw:
        # Process all raw files
        path = save_location / f'Memristor_data_{timestamp}.h5'
        process_files_raw(txt_files_base, base_dir, path)

    if calculate_curated:
        # Process curated files
        path = save_location / f'Curated_data_{timestamp}.h5'
        process_files_curated(txt_files_curated, base_curated, path)



if __name__ == '__main__':
    main(base_dir, base_curated, calculate_raw, calculate_curated, save_location)
