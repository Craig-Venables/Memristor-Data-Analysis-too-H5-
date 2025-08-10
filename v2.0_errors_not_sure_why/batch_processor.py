from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime
import subprocess
import sys


class BatchProcessor:
    """Handle batch processing of multiple datasets"""

    def __init__(self, base_config: ProcessingConfig):
        self.base_config = base_config

    def create_batch_config(self, datasets: List[Dict[str, Path]]) -> Path:
        """Create configuration file for batch processing"""
        batch_config = {
            'timestamp': datetime.now().isoformat(),
            'datasets': []
        }

        for dataset in datasets:
            config_dict = {
                'name': dataset['name'],
                'base_dir': str(dataset['base_dir']),
                'output_name': dataset.get('output_name', f"{dataset['name']}_processed.h5"),
                'config': self.base_config.__dict__
            }
            batch_config['datasets'].append(config_dict)

        # Save batch configuration
        batch_file = self.base_config.save_location / f"batch_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_config, f, indent=4)

        return batch_file

    def process_batch(self, batch_config_file: Path):
        """Process multiple datasets based on batch configuration"""
        with open(batch_config_file, 'r') as f:
            batch_config = json.load(f)

        results = []
        for dataset in batch_config['datasets']:
            print(f"\nProcessing dataset: {dataset['name']}")
            print("-" * 50)

            try:
                # Update configuration
                config = ProcessingConfig(**dataset['config'])
                config.base_dir = Path(dataset['base_dir'])
                config.raw_hdf5_name = dataset['output_name']

                # Process dataset
                processor = FileProcessor(config)
                processor.process_files()

                results.append({
                    'dataset': dataset['name'],
                    'status': 'success',
                    'output_file': str(config.save_location / config.raw_hdf5_name)
                })

            except Exception as e:
                results.append({
                    'dataset': dataset['name'],
                    'status': 'failed',
                    'error': str(e)
                })

        # Save results
        results_file = batch_config_file.parent / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=4)

        return results