from pathlib import Path

from main import process_files_raw, process_files_currated  # type: ignore


def run_raw_processing(base_dir: Path, save_path: Path, plot: bool = False) -> None:
    """Programmatically process raw files into an HDF5 file.

    - base_dir: root directory to scan for .txt files (depth 6)
    - save_path: HDF5 file path to write into
    - plot: whether to save figures per file
    """
    import main as v1_main

    v1_main.PLOT_GRAPHS = plot
    txt_files = [f for f in base_dir.rglob('*.txt') if len(f.relative_to(base_dir).parts) == 6]
    process_files_raw(txt_files, base_dir, save_path)


def run_curated_processing(base_dir: Path, save_path: Path, plot: bool = False) -> None:
    """Programmatically process curated files into an HDF5 file."""
    import main as v1_main

    v1_main.PLOT_GRAPHS = plot
    txt_files = [f for f in base_dir.rglob('*.txt') if len(f.relative_to(base_dir).parts) == 6]
    process_files_currated(txt_files, base_dir, save_path)


