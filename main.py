import pandas as pd
from pathlib import Path
from file_processing import file_analysis

# Set up base directory dynamically (you can change this environment variable for different systems)
user_dir = Path.home()  # Home directory of the user (works on any OS)

# Construct the base path relative to the home directory or environment variable
base_dir = user_dir / Path("OneDrive - The University of Nottingham/Documents/Phd/2) Data/1) Devices/1) Memristors")

# Recursively find all .txt files in the folder and subfolders
txt_files = base_dir.rglob('*.txt')

# Open an HDF5 file for writing (or appending to if it exists)
with pd.HDFStore('memristor_data.h5') as store:
    for file in txt_files:
        relative_path = file.relative_to(base_dir)
        depth = len(relative_path.parts)

        # Only process files at depth 6 (adjust as needed)
        if depth == 6:
            filename = file.name  # Depth 6 -> Filename
            device = relative_path.parts[4]  # Depth 5 -> Device
            section = relative_path.parts[3]  # Depth 4 -> Section
            sample = relative_path.parts[2]  # Depth 3 -> Sample
            material = relative_path.parts[1]  # Depth 2 -> Material

            # Read the file into a DataFrame
            try:
                # Try reading with appropriate delimiter (adjust as needed)
                df = pd.read_csv(file, delim_whitespace=True, header=0)

                # If 'voltage current' is one column, split it into 'voltage' and 'current'
                if 'voltage current' in df.columns:
                    df[['voltage', 'current']] = df['voltage current'].str.split(expand=True)
                    df.drop(columns=['voltage current'], inplace=True)

            except Exception as e:
                print(f"Error reading file {file}: {e}")
                continue  # Skip this file if there are errors

            if df is not None and not df.empty:
                # Add metadata as new columns to the DataFrame
                df['Material'] = material
                df['Sample'] = sample
                df['Section'] = section
                df['Device'] = device
                df['Filename'] = filename

                # Call the file_analysis function and pass the DataFrame
                processed_df = file_analysis(
                    df=df,  # Pass the DataFrame directly
                    plot_graph=False,  # Set to True if you want to plot
                    save_df=False,  # We don't need to save CSV, we're saving to HDF5
                    device_path=base_dir / device,  # Base path of the device
                    re_save_graph=False,  # Control graph re-saving
                    short_name=filename,  # Short name of the file
                    long_name=f"{filename}.csv"  # Long name (output filename)
                )

                if processed_df is not None and not processed_df.empty:
                    # Add the processed DataFrame to the HDF5 file
                    key = f'/{material}/{sample}/{section}/{device}/{filename}_processed'
                    store.put(key, processed_df)
                    print(f"Saved processed data for {filename} under {key}")
