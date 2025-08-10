from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json


@dataclass
class ProcessingConfig:
    """Configuration for data_analyzer.py processing pipeline"""
    calculate_raw: bool = True
    calculate_curated: bool = False
    force_recalculate: bool = True
    print_interval: int = 10
    debugging: bool = False
    plot_graphs: bool = False

    # File names
    output_file: str = "skipped_files.txt"
    summary_file: str = "device_metrics_summary.txt"
    output_file_curated: str = "skipped_files_curated.txt"
    summary_file_curated: str = "device_metrics_summary_curated.txt"

    # HDF5 file names
    raw_hdf5_name: str = "Memristor_data12.05.25.h5"
    curated_hdf5_name: str = "Curated_data.h5"

    # Paths (will be set in __post_init__)
    base_dir: Optional[Path] = None
    base_curated: Optional[Path] = None
    save_location: Optional[Path] = None
    excel_path: Optional[Path] = None

    def __post_init__(self):
        user_dir = Path.home()

        if self.debugging:
            self.base_dir = user_dir / "OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Memristors"
            self.base_curated = user_dir / "OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Curated Data"
        else:
            self.base_dir = user_dir / "OneDrive - The University of Nottingham/Documents/Phd/2) Data/1) Devices/1) Memristors"
            self.base_curated = user_dir / "OneDrive - The University of Nottingham/Desktop/Origin Test Folder/1) Curated Data"

        self.save_location = user_dir / "OneDrive - The University of Nottingham/Documents/Phd/1) Projects/1) Memristors/4) Code analysis"
        self.excel_path = user_dir / "OneDrive - The University of Nottingham/Documents/Phd/solutions and devices.xlsx"

    def save_to_json(self, filepath: Path):
        """Save configuration to JSON file"""
        config_dict = {k: str(v) if isinstance(v, Path) else v
                       for k, v in self.__dict__.items()}
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=4)

    @classmethod
    def load_from_json(cls, filepath: Path):
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)

        # Convert string paths back to Path objects
        path_fields = ['base_dir', 'base_curated', 'save_location', 'excel_path']
        for field in path_fields:
            if field in config_dict and config_dict[field]:
                config_dict[field] = Path(config_dict[field])

        return cls(**config_dict)