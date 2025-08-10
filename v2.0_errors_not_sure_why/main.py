import logging
import warnings
from pathlib import Path
import argparse
from datetime import datetime
try:
    from tables import NaturalNameWarning
except Exception:
    class NaturalNameWarning(Warning):
        pass

from config import ProcessingConfig
from file_processor import FileProcessor

# Suppress specific warnings
warnings.filterwarnings('ignore', category=NaturalNameWarning)


def setup_argparse():
    """Setup command line arguments"""
    parser = argparse.ArgumentParser(description='Process memristor data_analyzer.py files')
    parser.add_argument('--raw', action='store_true', default=True,
                        help='Process raw data_analyzer.py files')
    parser.add_argument('--curated', action='store_true', default=False,
                        help='Process curated data_analyzer.py files')
    parser.add_argument('--force', action='store_true', default=True,
                        help='Force recalculation of existing data_analyzer.py')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug mode')
    parser.add_argument('--parallel', action='store_true', default=False,
                        help='Enable parallel processing')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of parallel workers')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to configuration JSON file')
    parser.add_argument('--plot', action='store_true', default=False,
                        help='Enable plotting and save figures')
    return parser


def main():
    """Main entry point for the data_analyzer.py processing pipeline"""

    # Parse command line arguments
    parser = setup_argparse()
    args = parser.parse_args()

    # Load or create configuration
    if args.config and Path(args.config).exists():
        config = ProcessingConfig.load_from_json(Path(args.config))
    else:
        config = ProcessingConfig(
            calculate_raw=args.raw,
            calculate_curated=args.curated,
            force_recalculate=args.force,
            debugging=args.debug,
            plot_graphs=args.plot
        )

    # Save configuration for reproducibility
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config_path = config.save_location / f'config_{timestamp}.json'
    config.save_to_json(config_path)

    # Initialize processor
    processor = FileProcessor(config)

    # Process files
    print(f"Starting processing at {datetime.now()}")
    processor.process_files(parallel=args.parallel, max_workers=args.workers)

    # Generate yield report
    print("\nGenerating yield report...")
    yield_report = processor.generate_device_yield_report()
    yield_report_path = config.save_location / f'yield_report_{timestamp}.csv'
    yield_report.to_csv(yield_report_path, index=False)
    print(f"Yield report saved to: {yield_report_path}")

    print(f"\nProcessing completed at {datetime.now()}")


if __name__ == '__main__':
    main()