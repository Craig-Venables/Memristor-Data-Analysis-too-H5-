import pandas as pd
import numpy as np
from pathlib import Path
import h5py
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

class DataAnalyzer:
    """Class for analyzing processed data from HDF5 files"""

    def __init__(self, hdf5_path: Path):
        self.hdf5_path = hdf5_path

    def get_summary_statistics(self, material: str = None,
                             sample: str = None) -> pd.DataFrame:
        """Get summary statistics for specified material/sample"""
        data = []

        with h5py.File(self.hdf5_path, 'r') as f:
            for mat_key in f.keys():
                if material and mat_key != material:
                    continue

                for sample_key in f[mat_key].keys():
                    if sample and sample_key != sample:
                        continue

                    if '_info' in sample_key or '_yield' in sample_key:
                        continue

                    # Process each device
                    sample_data = self._analyze_sample(f[mat_key][sample_key])
                    sample_data['material'] = mat_key
                    sample_data['sample'] = sample_key
                    data.append(sample_data)

        return pd.DataFrame(data)

    def _analyze_sample(self, sample_group: h5py.Group) -> Dict:
        """Analyze a single sample"""
        on_off_ratios = []
        resistances_on = []
        resistances_off = []

        for section_key in sample_group.keys():
            for device_key in sample_group[section_key].keys():
                for dataset_key in sample_group[section_key][device_key].keys():
                    if '_info' in dataset_key:
                        data = sample_group[section_key][device_key][dataset_key][()]
                        df = pd.DataFrame(data)

                        if 'ON_OFF_Ratio' in df.columns:
                            on_off_ratios.append(df['ON_OFF_Ratio'].iloc[0])
                        if 'resistance_on_value' in df.columns:
                            resistances_on.append(df['resistance_on_value'].iloc[0])
                        if 'resistance_off_value' in df.columns:
                            resistances_off.append(df['resistance_off_value'].iloc[0])

        return {
            'num_devices': len(on_off_ratios),
            'avg_on_off_ratio': np.mean(on_off_ratios) if on_off_ratios else 0,
            'std_on_off_ratio': np.std(on_off_ratios) if on_off_ratios else 0,
            'avg_resistance_on': np.mean(resistances_on) if resistances_on else 0,
            'avg_resistance_off': np.mean(resistances_off) if resistances_off else 0,
            'yield_percentage': len([r for r in on_off_ratios if r > 10]) / len(on_off_ratios) * 100 if on_off_ratios else 0
        }

    def plot_distribution(self, metric: str = 'ON_OFF_Ratio',
                         log_scale: bool = True) -> plt.Figure:
        """Plot distribution of a specific metric"""
        values = []
        labels = []

        with h5py.File(self.hdf5_path, 'r') as f:
            for mat_key in f.keys():
                for sample_key in f[mat_key].keys():
                    if '_info' in sample_key or '_yield' in sample_key:
                        continue

                    sample_values = self._extract_metric_values(
                        f[mat_key][sample_key], metric
                    )
                    values.extend(sample_values)
                    labels.extend([f"{mat_key}-{sample_key}"] * len(sample_values))

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        df_plot = pd.DataFrame({'value': values, 'label': labels})

        if log_scale:
            df_plot['value'] = np.log10(df_plot['value'])
            ax.set_xlabel(f'Log10({metric})')
        else:
            ax.set_xlabel(metric)

        sns.boxplot(data=df_plot, x='label', y='value', ax=ax)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_title(f'Distribution of {metric} by Sample')

        plt.tight_layout()
        return fig

    def _extract_metric_values(self, sample_group: h5py.Group,
                              metric: str) -> List[float]:
        """Extract values for a specific metric from sample"""
        values = []

        for section_key in sample_group.keys():
            for device_key in sample_group[section_key].keys():
                for dataset_key in sample_group[section_key][device_key].keys():
                    if '_info' in dataset_key:
                        data = sample_group[section_key][device_key][dataset_key][()]
                        df = pd.DataFrame(data)

                        if metric in df.columns:
                            values.append(df[metric].iloc[0])

        return values



