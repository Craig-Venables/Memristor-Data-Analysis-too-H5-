def filter_data_by_sample(hdf5_file, sample_name):
    with pd.HDFStore(hdf5_file, mode='r') as store:
        # Filter all keys containing the sample name
        sample_keys = [key for key in store.keys() if sample_name in key and key.endswith('_metrics')]

        # List of data_analyzer.py for all the keys that match the sample
        data_list = []

        for key in sample_keys:
            data = store[key]  # Load data_analyzer.py for each key
            data_list.append(data)
            print(f"Loaded data for key: {key}")

        # Combine all data_analyzer.py into a single DataFrame (if they have the same structure)
        if data_list:
            combined_data = pd.concat(data_list, ignore_index=True)
            print(f"Combined data for sample {sample_name}:")
            print(combined_data.head())  # Show the first few rows of the combined data_analyzer.py

            return combined_data
        else:
            print(f"No data found for sample {sample_name}.")
            return None


# Example usage: Filter data_analyzer.py for sample "D65-0.05mgml-ITO-PMMA(3%)-Gold-s5"
sample_name = 'D65-0.05mgml-ITO-PMMA(3%)-Gold-s5'
sample_data = filter_data_by_sample(hdf5_file, sample_name)