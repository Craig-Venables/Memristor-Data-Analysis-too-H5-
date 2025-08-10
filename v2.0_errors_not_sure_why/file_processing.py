import pandas as pd
import numpy as np
import h5py
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

from equations import (absolute_val, current_density_eq, resistance,
                       electric_field_eq, inverse_resistance_eq, sqrt_array,
                       zero_devision_check, log_value, filter_positive_values,
                       filter_negative_values)
from metrics_calculation import (calculate_metrics_for_loops, area_under_curves,
                                 on_off_values)
from plotting import plot_loop_data, plot_single_sweep_data
from helpers import (check_for_loops, extract_folder_names,
                     check_if_folder_exists, split_iv_sweep,
                     dataframe_to_structured_array)


class FileAnalyzer:
    """Class to handle file analysis operations"""

    @staticmethod
    def analyze_iv_sweep(df: pd.DataFrame, plot_graph: bool = False,
                         save_df: bool = False, device_path: Optional[str] = None,
                         re_save_graph: bool = False, short_name: str = "",
                         long_name: str = "") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze IV sweep data_analyzer.py"""

        # Extract voltage and current data_analyzer.py
        v_data = df['voltage'].values
        c_data = df['current'].values

        # Filter positive and negative values
        v_data_ps, c_data_ps = filter_positive_values(v_data, c_data)
        v_data_ng, c_data_ng = filter_negative_values(v_data, c_data)

        # Check for multiple sweeps
        num_sweeps = check_for_loops(v_data)
        # Ensure integer and safe bounds
        try:
            num_sweeps_int = max(1, int(round(float(num_sweeps))))
        except Exception:
            num_sweeps_int = 1

        # Create metrics DataFrame
        metrics_df = FileAnalyzer._create_metrics_dataframe(
            v_data, c_data, v_data_ps, c_data_ps, v_data_ng, c_data_ng
        )

        # Process based on number of sweeps
        if num_sweeps_int > 1:
            df_file_stats = FileAnalyzer._process_multiple_sweeps(
                metrics_df, num_sweeps_int, device_path, plot_graph, re_save_graph
            )
        else:
            df_file_stats = FileAnalyzer._process_single_sweep(
                metrics_df, device_path, plot_graph, re_save_graph
            )

        return df_file_stats, metrics_df

    @staticmethod
    def analyze_endurance(df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze endurance data_analyzer.py"""
        # TODO: Implement endurance analysis
        print("Endurance analysis not yet implemented")
        return pd.DataFrame(), pd.DataFrame()

    @staticmethod
    def analyze_retention(df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze retention data_analyzer.py"""
        # TODO: Implement retention analysis
        print("Retention analysis not yet implemented")
        return pd.DataFrame(), pd.DataFrame()

    @staticmethod
    def _create_metrics_dataframe(v_data, c_data, v_data_ps, c_data_ps,
                                  v_data_ng, c_data_ng) -> pd.DataFrame:
        """Create DataFrame with calculated metrics"""

        # Calculate all metrics
        metrics = {
            'voltage': v_data,
            'current': c_data,
            'abs_current': absolute_val(c_data),
            'resistance': resistance(v_data, c_data),
            'voltage_ps': v_data_ps,
            'current_ps': c_data_ps,
            'voltage_ng': v_data_ng,
            'current_ng': c_data_ng,
            'log_Resistance': log_value(resistance(v_data, c_data)),
            'abs_Current_ps': absolute_val(c_data_ps),
            'abs_Current_ng': absolute_val(c_data_ng),
            'current_Density_ps': current_density_eq(v_data_ps, c_data_ps),
            'current_Density_ng': current_density_eq(v_data_ng, c_data_ng),
            'electric_field_ps': electric_field_eq(v_data_ps),
            'electric_field_ng': electric_field_eq(v_data_ng),
            'inverse_resistance_ps': inverse_resistance_eq(v_data_ps, c_data_ps),
            'inverse_resistance_ng': inverse_resistance_eq(v_data_ng, c_data_ng),
            'sqrt_Voltage_ps': sqrt_array(v_data_ps),
            'sqrt_Voltage_ng': sqrt_array(v_data_ng),
        }

        return pd.DataFrame(metrics).dropna()

    @staticmethod
    def _process_multiple_sweeps(df: pd.DataFrame, num_sweeps: int,
                                 device_path: Optional[str], plot_graph: bool,
                                 re_save_graph: bool) -> pd.DataFrame:
        """Process data_analyzer.py with multiple sweeps"""

        # Split loop data_analyzer.py
        split_v_data, split_c_data = FileAnalyzer._split_loops(
            df['voltage'].values, df['current'].values, num_sweeps
        )

        # Calculate metrics for multiple sweeps
        metrics = calculate_metrics_for_loops(split_v_data, split_c_data)
        ps_areas, ng_areas, areas, normalized_areas, ron, roff, von, voff = metrics

        # Calculate averages
        file_stats = {
            'ps_area_avg': np.mean(ps_areas),
            'ng_area_avg': np.mean(ng_areas),
            'areas_avg': np.mean(areas),
            'normalized_areas_avg': np.mean(normalized_areas),
            'resistance_on_value': np.mean(ron),
            'resistance_off_value': np.mean(roff),
            'ON_OFF_Ratio': zero_devision_check(np.mean(ron), np.mean(roff)),
            'voltage_on_value': np.mean(von),
            'voltage_off_value': np.mean(voff),
            'num_sweeps': num_sweeps,
            'ps_area_std': np.std(ps_areas),
            'ng_area_std': np.std(ng_areas),
            'ron_std': np.std(ron),
            'roff_std': np.std(roff),
        }

        # Plotting
        if plot_graph and device_path:
            plot_single_sweep_data(df, None, device_path, re_save_graph)
            plot_loop_data(split_v_data, split_c_data, None, device_path, re_save_graph)

        return pd.DataFrame([file_stats])

    @staticmethod
    def _process_single_sweep(df: pd.DataFrame, device_path: Optional[str],
                              plot_graph: bool, re_save_graph: bool) -> pd.DataFrame:
        """Process data_analyzer.py with single sweep"""

        # Calculate metrics
        ps_area, ng_area, area, normalized_area = area_under_curves(
            df['voltage'].values, df['current'].values
        )
        ron, roff, von, voff = on_off_values(
            df['voltage'].values, df['current'].values
        )

        # Store metrics
        file_stats = {
            'ps_area': ps_area,
            'ng_area': ng_area,
            'area': area,
            'normalized_area': normalized_area,
            'resistance_on_value': ron,
            'resistance_off_value': roff,
            'ON_OFF_Ratio': zero_devision_check(ron, roff),
            'voltage_on_value': von,
            'voltage_off_value': voff,
            'num_sweeps': 1,
        }

        # Plotting
        if plot_graph and device_path:
            plot_single_sweep_data(df, None, device_path, re_save_graph)

        return pd.DataFrame([file_stats])

    @staticmethod
    def _split_loops(v_data: np.ndarray, c_data: np.ndarray,
                     num_loops: int) -> Tuple[list, list]:
        """Split looped data_analyzer.py into individual sweeps"""
        total_length = len(v_data)
        # Guard against non-integers/zeros
        try:
            num_loops = max(1, int(num_loops))
        except Exception:
            num_loops = 1
        size = max(1, total_length // num_loops)

        # Handle remainder
        if total_length % num_loops != 0:
            size += 1

        split_v_data = [v_data[i:i + size] for i in range(0, total_length, size)]
        split_c_data = [c_data[i:i + size] for i in range(0, total_length, size)]

        return split_v_data[:num_loops], split_c_data[:num_loops]


def read_file_to_dataframe(file: Path) -> Optional[pd.DataFrame]:
    """Read a text file and convert to DataFrame"""
    try:
        # Read file with flexible whitespace separator
        df = pd.read_csv(file, sep='\s+', header=0)

        # Normalize column names
        df.columns = [col.lower() for col in df.columns]

        # Handle combined columns
        target_col = next(
            (col for col in df.columns if 'voltage' in col and 'current' in col),
            None
        )

        if target_col:
            # Split the combined column
            split_values = df[target_col].str.split(expand=True)

            if "time" in target_col and split_values.shape[1] >= 3:
                df[['voltage', 'current', 'time']] = split_values.iloc[:, :3]
            else:
                df[['voltage', 'current']] = split_values.iloc[:, :2]

            df.drop(columns=[target_col], inplace=True)

        # Convert to numeric
        for col in ['voltage', 'current']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows with NaN values
        df = df.dropna(subset=['voltage', 'current'])

        return df

    except Exception as e:
        print(f"Error reading file {file}: {e}")
        return None


def add_metadata(df: pd.DataFrame, material: str, sample: str,
                 section: str, device: str, filename: str) -> None:
    """Add metadata columns to DataFrame"""
    metadata = {
        'Material': material,
        'Sample': sample,
        'Section': section,
        'Device': device,
        'Filename': filename
    }

    for key, value in metadata.items():
        df[key] = value


def analyze_file(sweep_type: str, analysis_params: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze file based on sweep type"""
    analyzer = FileAnalyzer()

    sweep_type_map = {
        'Iv_sweep': analyzer.analyze_iv_sweep,
        'Endurance': analyzer.analyze_endurance,
        'Retention': analyzer.analyze_retention,
    }

    if sweep_type in sweep_type_map:
        return sweep_type_map[sweep_type](**analysis_params)
    else:
        return pd.DataFrame(), pd.DataFrame()


def save_to_hdf5(store: h5py.File, key_file_stats: str, key_raw_data: str,
                 df_file_stats: pd.DataFrame, df_raw_data: pd.DataFrame) -> None:
    """Save DataFrames to HDF5 file"""

    # Convert DataFrames to structured arrays
    structured_raw_data = dataframe_to_structured_array(df_raw_data)
    structured_file_stats = dataframe_to_structured_array(df_file_stats)

    # Check if keys exist and delete if force recalculate
    for key, data in [(key_raw_data, structured_raw_data),
                      (key_file_stats, structured_file_stats)]:
        if key in store:
            del store[key]

        # Create dataset with compression
        store.create_dataset(
            key,
            data=data,
            compression="gzip",
            compression_opts=9,
            dtype=data.dtype
        )


def load_from_hdf5(store_path: Path, key: str) -> Optional[pd.DataFrame]:
    """Load data_analyzer.py from HDF5 file"""
    try:
        with h5py.File(store_path, 'r') as f:
            if key in f:
                data = f[key][()]
                # Convert structured array back to DataFrame
                if hasattr(data, 'dtype') and data.dtype.names:
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame(data)
            else:
                return None
    except Exception as e:
        print(f"Error loading from HDF5: {e}")
        return None


