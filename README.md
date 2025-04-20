# Memristor Data Analysis Pipeline

## Overview
This project implements a comprehensive data analysis pipeline for processing and analyzing memristor device measurements. The pipeline handles raw data files, performs various calculations, and stores the processed data in HDF5 format.

## Key Features
- Processing of raw measurement data files
- Multiple sweep type support (IV sweeps, endurance, retention) 
- Automated device classification
- HDF5 data storage with compression
- Excel integration for device metadata
- Progress tracking and error handling
- Support for both single and multiple sweep measurements

## Project Structure

├── main.py # Main execution script/

├── file_processing.py # Core file processing functions $
├── metrics_calculation.py # Metrics calculation utilities
├── helpers.py # Helper functions
└── excell.py # Excel file handling

## Usage

### Configuration
Configure the input parameters in main.py:
```python
calculate_raw = True       # Process raw files
calculate_currated = False # Process curated files  
FORCE_RECALCULATE = True  # Force reprocessing of existing data
```
## set paths 
```python
base_dir = Path("path/to/raw/data")
base_currated = Path("path/to/curated/data")
save_location = Path("path/to/output")
```

### Data Processing Flow
1. File Discovery
Scans input directories for .txt files
Validates file structure and depth
2. Data Processing
Reads raw measurement data
Performs calculations and metric extraction
Adds metadata and classification
3. Storage
Saves processed data to HDF5 files
Maintains file hierarchy
Implements data compression
Output
The pipeline generates:

HDF5 files containing processed data
Summary statistics
Skipped file reports
Device metrics summaries
Dependencies
pandas
h5py
numpy
pathlib
warnings
Error Handling
The pipeline includes comprehensive error handling for:

Missing files
Invalid data formats
NaN values
Unknown sweep types
File access issues
Notes
Ensure proper file hierarchy (6 levels deep) for raw data
Excel files must be properly formatted for metadata extraction
HDF5 files are compressed to optimize storage
Contributing
For contributions or issues, please contact the repository maintainers.