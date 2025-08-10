## Memristor Data Analysis (v1)

### Overview
This repository processes memristor device measurement text files, computes metrics (e.g., ON/OFF ratios, areas, resistances), enriches with metadata/classification from Excel, and writes results to compressed HDF5 files. This README documents the v1 flow (`main.py`).

### Key capabilities
- IV sweep processing (multi-sweep aware) with derived metrics
- Curated data pipeline scaffold (same storage format)
- Device classification via per-device Excel sheets
- Fabrication/solutions metadata lookup via a master Excel workbook
- HDF5 storage using a hierarchical layout and compression
- Skipped-file and processing summaries; optional yield report (v2.0)

## Project layout (v1)
- `main.py`: Entry point for processing
- `file_processing.py`, `metrics_calculation.py`, `helpers.py`, `plotting.py`: Processing utilities
- `excell.py`: Excel integrations (master workbook + per-device workbook)
- `api.py`: Simple wrapper to call v1 from other scripts

## Data assumptions
- Input file tree depth is 6: `nanoparticles/material/sample/section/device/filename.txt`
- Text files contain two columns (voltage, current) or a combined column that includes both (optionally time)
- Excel files:
  - Master workbook: `solutions and devices.xlsx` (required for fabrication/solutions metadata)
  - Per-device workbook: one Excel file per sample in the sample folder, used for device classification

## Output structure
HDF5 keys follow the source hierarchy and store two datasets per file:
- `/{material}/{sample}/{section}/{device}/{filename}_file_stats`
- `/{material}/{sample}/{section}/{device}/{filename}_raw_data`

All datasets are compressed (gzip). Text/object columns are stored as UTF‑8 strings.

## How to run (v1)
Edit the paths/flags near the top of `main.py` (they default to user home/OneDrive layouts). Then run:

```bash
python main.py
```

Flags in `main.py`:
- `calculate_raw`: process raw data (default True)
- `calculate_curated`: process curated data (default False)
- `FORCE_RECALCULATE`: overwrite existing HDF5 datasets (default True)
 - `PLOT_GRAPHS`: save per-file figures (default False)

Outputs are written to `save_location` as date-stamped files, e.g. `Memristor_data_YYYYMMDD.h5` and `Curated_data_YYYYMMDD.h5`. Skipped files and summaries are saved alongside.

### Import from another script
Use `api.py` to call v1 programmatically:

```python
from pathlib import Path
from api import run_raw_processing, run_curated_processing

run_raw_processing(Path("/path/to/raw"), Path("/path/to/output.h5"), plot=False)
# or
run_curated_processing(Path("/path/to/curated"), Path("/path/to/curated_output.h5"), plot=False)
```

## Configuration
### Paths and filenames
Both `main.py` and `v2.0/config.py` set defaults relative to `Path.home()`. Update to match your environment if you are not using the same OneDrive structure.

In `v2.0/config.py` you can save and reuse a configuration JSON:
```bash
python v2.0/main.py --raw --force
# A timestamped config JSON is written to save_location; or provide your own via --config
```

## Dependencies
Python 3.10+ recommended.

Core:
- `pandas`, `numpy`, `h5py`

Excel integration:
- `openpyxl`

Plotting (optional):
- `matplotlib`, `Pillow`

Install example:
```bash
pip install pandas numpy h5py openpyxl matplotlib seaborn scipy tqdm pillow
# Optional
pip install tables
```

## What the pipeline does (step-by-step)
1. Discover `.txt` files at the expected depth under the base directory
2. Detect sweep type via header/content heuristics (IV supported; endurance/retention scaffolds exist)
3. Parse data, normalize columns, coerce to numeric, drop invalid rows
4. Compute metrics (areas, ON/OFF ratio, resistances, etc.), handling multi-sweep files
5. Attach metadata (material, sample, section, device, filename)
6. Lookup fabrication/solutions info and device classification from Excel
7. Write per-file datasets to HDF5 with compression
8. Emit summaries: skipped files, device counts

## Known limitations / notes
- Endurance/retention analysis functions are placeholders
- Sweep-loop detection is heuristic and may need tolerance tuning for noisy data
- Curated flow is supported but less exercised than raw flow
- HDF5 uses suffix-based dataset names; you can switch to group-based layout if desired

## Troubleshooting
- “tables could not be resolved”: PyTables is optional; warnings are safely handled
- Excel parsing errors: ensure sheet names match those expected in `excell.py`
- Missing data in HDF5: confirm file path depth (must be 6) and the sweep type detection

## Related scripts and their roles
- `file_processing.py`: read/parse files, compute metrics, save to HDF5
- `metrics_calculation.py`: numerical metrics and utilities
- `helpers.py`: sweep detection, HDF5 key generation, NaN checks, string-safe structured arrays for HDF5
- `plotting.py`: plotting for IV and derived plots (enable via `PLOT_GRAPHS` in `main.py`)
- `excell.py`: master workbook lookup and per-device classification
- `api.py`: wrapper for calling v1 processing from other scripts

## License
Not specified. If you plan to share or publish, add an explicit license.