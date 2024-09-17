import pandas as pd
from pathlib import Path
from file_processing import file_analysis, file_analysis_endurance, file_analysis_retention
import warnings
from tables import NaturalNameWarning
from helpers import check_sweep_type  # Assuming this function is in check_sweep_type.py


warnings.filterwarnings('ignore', category=NaturalNameWarning)

# Helper function to check if the DataFrame contains NaN values
def check_for_nan(df):
    if df.isna().values.any():
        print("File contains NaN values. Skipping...")
        return True
    return False

# Function to generate parameters for file_analysis
def generate_analysis_params(df, filename, base_dir, device):
    """ Generate a dictionary of parameters to be passed to file_analysis """
    return {
        'df': df,
        'plot_graph': False,            # Set to True if you want to plot
        'save_df': False,               # We don't need to save CSV, we're saving to HDF5
        'device_path': base_dir / device,  # Base path of the device
        're_save_graph': False,         # Control graph re-saving
        'short_name': filename,         # Short name of the file
        'long_name': f"{filename}.csv"  # Long name (output filename)
    }

# Set up base directory dynamically (you can change this environment variable for different systems)
user_dir = Path.home()  # Home directory of the user (works on any OS)

# Construct the base path relative to the home directory or environment variable
# base_dir = user_dir / Path("OneDrive - The University of Nottingham/Documents/Phd/2) Data/1) Devices/1) Memristors")
# testing
base_dir = user_dir / Path("OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Memristors")

# Recursively find all .txt files in the folder and subfolders at depth 6
txt_files = list(f for f in base_dir.rglob('*.txt') if len(f.relative_to(base_dir).parts) == 6)

# Count total files for the completion percentage
total_files = len(txt_files)
processed_files = 0  # Track how many files have been processed

# Set a print interval (e.g., print progress every 5 files)
print_interval = 50

# Track the current sample to detect when it changes
current_sample = None

# Output file to store file paths that are skipped
output_file = "skipped_files.txt"

# Open an HDF5 file for writing (or appending to if it exists)
with pd.HDFStore('memristor_data.h5') as store:
    for i, file in enumerate(txt_files, 1):  # Enumerate to get file index for progress tracking
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        # Only process files at depth 6 (already filtered, but double-checking)
        if depth == 6:
            filename = file.name             # Depth 6 -> Filename
            device = relative_path.parts[4]  # Depth 5 -> Device
            section = relative_path.parts[3] # Depth 4 -> Section
            sample = relative_path.parts[2]  # Depth 3 -> Sample
            material = relative_path.parts[1]# Depth 2 -> Material

            # Check if the sample has changed
            if sample != current_sample:
                current_sample = sample  # Update the current sample
                print(f"Moving on to new sample: {sample}")

            # Determine the file's sweep type using check_sweep_type
            sweep_type = check_sweep_type(file, output_file)

            # Skip files that don't match any expected sweep type
            if sweep_type is None:
                print(f"Skipping file {filename}, unknown sweep type.")
                continue

            # Read the file into a DataFrame
            try:
                # Try reading with appropriate delimiter (adjust as needed)
                df = pd.read_csv(file, sep='\s+', header=0)

                # If 'voltage current' is one column, split it into 'voltage' and 'current'
                if 'voltage current' in df.columns:
                    df[['voltage', 'current']] = df['voltage current'].str.split(expand=True)
                    df.drop(columns=['voltage current'], inplace=True)

            except Exception as e:
                print(f"Error reading file {file}: {e}")
                continue  # Skip this file if there are errors

            # Skip if DataFrame contains NaN values
            if check_for_nan(df):
                continue

            if df is not None and not df.empty:
                # Add metadata as new columns to the DataFrame
                df['Material'] = material
                df['Sample'] = sample
                df['Section'] = section
                df['Device'] = device
                df['Filename'] = filename

                # Generate the parameters using the helper function
                analysis_params = generate_analysis_params(df, filename, base_dir, device)

                # Call the appropriate analysis function based on the file type
                if sweep_type == 'Iv_sweep':
                    df_file_stats, metrics_df = file_analysis(**analysis_params)
                elif sweep_type == 'Endurance':
                    df_file_stats, metrics_df = file_analysis_endurance(**analysis_params)
                elif sweep_type == 'Retention':
                    df_file_stats, metrics_df = file_analysis_retention(**analysis_params)  # Assuming this exists
                else:
                    #df_file_stats, metrics_df = file_analysis_other(**analysis_params)  # For other file types
                    pass

                if df_file_stats is not None and not df_file_stats.empty:
                    # Add the raw data DataFrame to the HDF5 file
                    key_raw = f'/{material}/{sample}/{section}/{device}/{filename}_raw'
                    store.put(key_raw, df_file_stats)
                    print(f"Saved raw data for {filename} under {key_raw}")

                if metrics_df is not None and not metrics_df.empty:
                    # Add the metrics DataFrame to the HDF5 file
                    key_metrics = f'/{material}/{sample}/{section}/{device}/{filename}_metrics'
                    store.put(key_metrics, metrics_df)
                    print(f"Saved metrics data for {filename} under {key_metrics}")

                # Increment the processed files count
                processed_files += 1

                # Print progress every X files
                if processed_files % print_interval == 0:
                    percent_completed = (processed_files / total_files) * 100
                    print(f"Processed {processed_files}/{total_files} files. {percent_completed:.2f}% done.")

    # Final percentage after all files have been processed
    percent_completed = (processed_files / total_files) * 100
    print(f"Processing complete: {processed_files}/{total_files} files. {percent_completed:.2f}% done.")