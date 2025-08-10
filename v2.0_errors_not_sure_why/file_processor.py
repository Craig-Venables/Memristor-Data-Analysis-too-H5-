import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import pandas as pd
import h5py
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from config import ProcessingConfig
from helpers import (generate_analysis_params, extract_file_info,
                     check_if_file_exists, check_for_nan, generate_hdf5_keys,
                     check_sweep_type, dataframe_to_structured_array)
from file_processing import (read_file_to_dataframe, add_metadata,
                             analyze_file, save_to_hdf5)
from excell import (save_info_from_solution_devices_excell,
                    save_info_from_device_into_excell, device_clasification)

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Track processing statistics"""
    total_files: int = 0
    processed_files: int = 0
    skipped_files: List[Path] = field(default_factory=list)
    device_file_counts: Dict[Tuple, int] = field(default_factory=dict)
    errors: List[Tuple[Path, str]] = field(default_factory=list)

    def add_processed_file(self):
        self.processed_files += 1

    def add_skipped_file(self, filepath: Path):
        self.skipped_files.append(filepath)

    def add_error(self, filepath: Path, error_msg: str):
        self.errors.append((filepath, error_msg))

    def update_device_count(self, device_key: Tuple):
        if device_key not in self.device_file_counts:
            self.device_file_counts[device_key] = 0
        self.device_file_counts[device_key] += 1

    def get_summary(self) -> str:
        missing = self.total_files - self.processed_files
        return (f"Processing complete: {self.processed_files}/{self.total_files} "
                f"files processed, with {missing} files missing")

    def get_error_summary(self) -> str:
        if not self.errors:
            return "No errors encountered"
        return f"Errors encountered: {len(self.errors)}"


class FileProcessor:
    """Main file processor class with improved features"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.setup_logging()
        self.current_sample_cache = {}  # Cache for sample information
        self._fabrication_written = set()  # Track (material, sample) written

    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # Create logs directory
        log_dir = self.config.save_location / 'logs'
        log_dir.mkdir(exist_ok=True)

        # Setup file handler
        log_file = log_dir / 'processing.log'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def process_files(self, parallel: bool = False, max_workers: int = None):
        """Main processing method with optional parallel processing"""
        if self.config.calculate_raw:
            self._process_raw_files(parallel, max_workers)

        if self.config.calculate_curated:
            self._process_curated_files(parallel, max_workers)

    def _process_raw_files(self, parallel: bool = False, max_workers: int = None):
        """Process raw data_analyzer.py files"""
        logger.info("Starting raw file processing")

        txt_files = self._get_files(self.config.base_dir, depth=6)
        stats = ProcessingStats(total_files=len(txt_files))

        hdf5_path = self.config.save_location / self.config.raw_hdf5_name

        if parallel:
            self._process_raw_files_parallel(txt_files, hdf5_path, stats, max_workers)
        else:
            self._process_raw_files_sequential(txt_files, hdf5_path, stats)

        self._save_processing_summary(stats, self.config.output_file)
        logger.info(stats.get_summary())
        logger.info(stats.get_error_summary())

    def _process_curated_files(self, parallel: bool = False, max_workers: int = None):
        """Process curated data files (sequential for stability)"""
        logger.info("Starting curated file processing")

        txt_files = self._get_files(self.config.base_curated, depth=6)
        stats = ProcessingStats(total_files=len(txt_files))

        hdf5_path = self.config.save_location \
            / self.config.curated_hdf5_name

        with h5py.File(hdf5_path, 'a') as store:
            for file in tqdm(txt_files, desc="Processing curated files"):
                try:
                    self._process_single_curated_file(file, store, stats)
                except Exception as e:
                    logger.error(f"Error processing curated file {file}: {str(e)}")
                    stats.add_error(file, str(e))

        self._save_processing_summary(stats, self.config.output_file_curated)
        logger.info(stats.get_summary())
        logger.info(stats.get_error_summary())

    def _process_raw_files_sequential(self, txt_files: List[Path],
                                      hdf5_path: Path, stats: ProcessingStats):
        """Process files sequentially with progress bar"""
        with h5py.File(hdf5_path, 'a') as store:
            for file in tqdm(txt_files, desc="Processing raw files"):
                try:
                    self._process_single_raw_file(file, store, stats)
                except Exception as e:
                    logger.error(f"Error processing file {file}: {str(e)}")
                    stats.add_error(file, str(e))

    def _process_raw_files_parallel(self, txt_files: List[Path],
                                    hdf5_path: Path, stats: ProcessingStats,
                                    max_workers: int = None):
        """Process files in parallel"""
        if max_workers is None:
            max_workers = multiprocessing.cpu_count() - 1

        # Process files in batches to avoid HDF5 conflicts
        batch_size = 100
        for i in range(0, len(txt_files), batch_size):
            batch = txt_files[i:i + batch_size]

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_file_batch, file): file
                    for file in batch
                }

                for future in tqdm(as_completed(futures), total=len(batch),
                                   desc=f"Processing batch {i // batch_size + 1}"):
                    file = futures[future]
                    try:
                        result = future.result()
                        if result:
                            # Save to HDF5
                            self._save_batch_results(hdf5_path, result)
                            stats.add_processed_file()
                    except Exception as e:
                        logger.error(f"Error processing file {file}: {str(e)}")
                        stats.add_error(file, str(e))

    def _process_file_batch(self, file: Path) -> Optional[Dict]:
        """Process a single file for batch processing"""
        try:
            relative_path = file.relative_to(self.config.base_dir)

            # Extract file information
            file_info = self._extract_file_info(relative_path)
            if not file_info:
                return None

            filename, device, section, sample, material, nano_particles = file_info

            # Skip combined plots
            if device == 'plots_combined':
                return None

            # Check sweep type
            sweep_type = check_sweep_type(file, self.config.output_file)
            if not sweep_type:
                return None

            # Read and validate data_analyzer.py
            df = read_file_to_dataframe(file)
            if df is None or check_for_nan(df):
                return None

            # Process the file
            add_metadata(df, material, sample, section, device, filename)
            analysis_params = generate_analysis_params(df, filename, self.config.base_dir, device)
            # Respect plotting flag
            analysis_params['plot_graph'] = self.config.plot_graphs

            df_file_stats, df_raw_data = analyze_file(sweep_type, analysis_params)

            if df_raw_data is not None:
                # Add classification
                classification = self._get_device_classification(
                    sample, section, device, material, nano_particles
                )
                df_raw_data['classification'] = classification

            # Generate keys
            key_file_stats, key_raw_data = generate_hdf5_keys(
                material, sample, section, device, filename
            )

            return {
                'key_file_stats': key_file_stats,
                'key_raw_data': key_raw_data,
                'df_file_stats': df_file_stats,
                'df_raw_data': df_raw_data,
                'device_key': (material, sample, section, device),
                'material': material,
                'sample': sample
            }

        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return None

    def _save_batch_results(self, hdf5_path: Path, result: Dict):
        """Save batch processing results to HDF5"""
        with h5py.File(hdf5_path, 'a') as store:
            # Write fabrication metadata once per (material, sample)
            self._maybe_write_fabrication(store, result['material'], result['sample'])
            save_to_hdf5(
                store,
                result['key_file_stats'],
                result['key_raw_data'],
                result['df_file_stats'],
                result['df_raw_data']
            )

    def _process_single_raw_file(self, file: Path, store: h5py.File,
                                 stats: ProcessingStats) -> Optional[bool]:
        """Process a single raw file"""
        relative_path = file.relative_to(self.config.base_dir)

        # Extract file information
        file_info = self._extract_file_info(relative_path)
        if not file_info:
            return None

        filename, device, section, sample, material, nano_particles = file_info

        # Skip combined plots
        if device == 'plots_combined':
            return None

        # Generate HDF5 keys
        # Generate HDF5 keys
        key_file_stats, key_raw_data = generate_hdf5_keys(
            material, sample, section, device, filename
        )

        # Check if already exists
        if not self.config.force_recalculate and check_if_file_exists(store, key_file_stats):
            logger.debug(f"File {filename} already exists in HDF5. Skipping...")
            return None

        # Check sweep type
        sweep_type = check_sweep_type(file, self.config.output_file)
        if not sweep_type:
            stats.add_skipped_file(file)
            return None

        # Read and validate data_analyzer.py
        df = read_file_to_dataframe(file)
        if df is None or check_for_nan(df):
            stats.add_skipped_file(file)
            return None

        # Process the file
        add_metadata(df, material, sample, section, device, filename)
        analysis_params = generate_analysis_params(df, filename, self.config.base_dir, device)
        analysis_params['plot_graph'] = self.config.plot_graphs

        df_file_stats, df_raw_data = analyze_file(sweep_type, analysis_params)

        if df_raw_data is not None:
            # Add classification
            classification = self._get_device_classification(
                sample, section, device, material, nano_particles
            )
            df_raw_data['classification'] = classification

        # Save fabrication metadata once per (material, sample)
        self._maybe_write_fabrication(store, material, sample)

        # Save to HDF5
        save_to_hdf5(store, key_file_stats, key_raw_data, df_file_stats, df_raw_data)

        # Update statistics
        device_key = (material, sample, section, device)
        stats.update_device_count(device_key)
        stats.add_processed_file()

        return True

    def _process_single_curated_file(self, file: Path, store: h5py.File,
                                     stats: ProcessingStats) -> Optional[bool]:
        """Process a single curated file"""
        relative_path = file.relative_to(self.config.base_curated)

        file_info = self._extract_file_info(relative_path)
        if not file_info:
            return None

        filename, device, section, sample, material, nano_particles = file_info

        # Skip combined plots
        if device == 'plots_combined':
            return None

        key_file_stats, key_raw_data = generate_hdf5_keys(
            material, sample, section, device, filename
        )

        if not self.config.force_recalculate and check_if_file_exists(store, key_file_stats):
            logger.debug(f"Curated {filename} already exists in HDF5. Skipping...")
            return None

        sweep_type = check_sweep_type(file, self.config.output_file_curated)
        if not sweep_type:
            stats.add_skipped_file(file)
            return None

        df = read_file_to_dataframe(file)
        if df is None or check_for_nan(df):
            stats.add_skipped_file(file)
            return None

        add_metadata(df, material, sample, section, device, filename)
        analysis_params = generate_analysis_params(df, filename, self.config.base_curated, device)
        analysis_params['plot_graph'] = self.config.plot_graphs

        df_file_stats, df_raw_data = analyze_file(sweep_type, analysis_params)

        # Save to HDF5
        save_to_hdf5(store, key_file_stats, key_raw_data, df_file_stats, df_raw_data)

        device_key = (material, sample, section, device)
        stats.update_device_count(device_key)
        stats.add_processed_file()

        return True

    def _maybe_write_fabrication(self, store: h5py.File, material: str, sample: str) -> None:
        """Write fabrication/solutions metadata to HDF5 once per (material, sample)."""
        key = (material, sample)
        if key in self._fabrication_written:
            return
        try:
            info = save_info_from_solution_devices_excell(sample, self.config.excel_path)
            if not info:
                self._fabrication_written.add(key)
                return
            # Convert dict to single-row DataFrame for storage
            df_info = pd.DataFrame([info])
            structured = dataframe_to_structured_array(df_info)
            dataset_key = f'/{material}/{sample}_fabrication'
            # Overwrite if exists (rare if force)
            if dataset_key in store:
                del store[dataset_key]
            store.create_dataset(dataset_key, data=structured, compression="gzip", dtype=structured.dtype)
        except Exception as e:
            logger.warning(f"Could not write fabrication metadata for {material}/{sample}: {e}")
        finally:
            self._fabrication_written.add(key)

    def _get_device_classification(self, sample: str, section: str,
                                   device: str, material: str,
                                   nano_particles: str) -> str:
        """Get device classification from Excel"""
        try:
            # Check cache first
            cache_key = f"{sample}_{section}_{device}"
            if cache_key in self.current_sample_cache:
                return self.current_sample_cache[cache_key]

            sample_location = self.config.base_dir / nano_particles / material / sample
            result = save_info_from_device_into_excell(sample, sample_location)
            classification = device_clasification(result, device, section, sample_location)

            # Cache the result
            self.current_sample_cache[cache_key] = classification

            return classification
        except Exception as e:
            logger.warning(f"Could not get classification: {str(e)}")
            return "unknown"

    def _extract_file_info(self, relative_path: Path) -> Optional[Tuple]:
        """Extract file information from path"""
        if len(relative_path.parts) != 6:
            return None

        filename = relative_path.parts[-1]
        device = relative_path.parts[4]
        section = relative_path.parts[3]
        sample = relative_path.parts[2]
        material = relative_path.parts[1]
        nanoparticles = relative_path.parts[0]

        return filename, device, section, sample, material, nanoparticles

    def _get_files(self, base_dir: Path, depth: int) -> List[Path]:
        """Get all text files at specified depth"""
        return list(f for f in base_dir.rglob('*.txt')
                    if len(f.relative_to(base_dir).parts) == depth)

    def _save_processing_summary(self, stats: ProcessingStats, output_file: str):
        """Save processing summary to file"""
        summary_path = self.config.save_location / output_file

        with open(summary_path, 'w') as f:
            f.write(stats.get_summary() + '\n\n')

            f.write("Device file counts:\n")
            for device_key, count in sorted(stats.device_file_counts.items()):
                f.write(f"{device_key}: {count} files\n")

            f.write("\nSkipped files:\n")
            for file in stats.skipped_files:
                f.write(f"{file}\n")

            if stats.errors:
                f.write("\nErrors:\n")
                for file, error in stats.errors:
                    f.write(f"{file}: {error}\n")

    def generate_device_yield_report(self) -> pd.DataFrame:
        """Generate a yield report for all devices"""
        hdf5_path = self.config.save_location / self.config.raw_hdf5_name
        yield_data = []

        with h5py.File(hdf5_path, 'r') as f:
            for material in f.keys():
                for sample in f[material].keys():
                    if '_yield' in sample:
                        continue

                    # Count devices and working devices
                    device_count = 0
                    working_count = 0

                    for section in f[material][sample].keys():
                        for device in f[material][sample][section].keys():
                            device_count += 1
                            # Check if device has valid data_analyzer.py
                            if self._is_device_working(f[material][sample][section][device]):
                                working_count += 1

                    yield_percent = (working_count / device_count * 100) if device_count > 0 else 0

                    yield_data.append({
                        'material': material,
                        'sample': sample,
                        'total_devices': device_count,
                        'working_devices': working_count,
                        'yield_percentage': yield_percent
                    })

        return pd.DataFrame(yield_data)

    def _is_device_working(self, device_group: h5py.Group) -> bool:
        """Check if a device is working based on its data_analyzer.py"""
        # Implement your logic here
        # For example, check if ON/OFF ratio > threshold
        try:
            for dataset_name in device_group.keys():
                if '_info' in dataset_name:
                    data = device_group[dataset_name][()]
                    # Convert structured array to DataFrame if needed
                    if hasattr(data, 'dtype') and data.dtype.names:
                        df = pd.DataFrame(data)
                        if 'ON_OFF_Ratio' in df.columns:
                            return df['ON_OFF_Ratio'].iloc[0] > 10  # Example threshold
            return False
        except:
            return False