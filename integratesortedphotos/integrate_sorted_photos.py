import argparse
import logging
import shutil
import os
from datetime import datetime
from tqdm import tqdm

def setup_logging(log_file, debug):
    """Set up logging configuration to log to both the specified log file and the console if debug is True."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename=log_file, filemode='a')

    if debug:
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        # Add the console handler to the root logger
        logging.getLogger().addHandler(console_handler)

    logging.debug('Logging has been set up.')

def copy_files_with_metadata(src, dst):
    """Copy files from src to dst while preserving metadata."""
    files_to_copy = []
    for root, _, files in os.walk(src):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst, os.path.relpath(src_file, src))
            files_to_copy.append((src_file, dst_file))

    for src_file, dst_file in tqdm(files_to_copy, desc="Copying files", unit="file"):
        dst_dir = os.path.dirname(dst_file)
        # Ensure the target directory exists
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        try:
            # Copy the file
            shutil.copy2(src_file, dst_file)
            logging.info(f'Copied {src_file} to {dst_file}')
        except Exception as e:
            logging.error(f'Failed to copy {src_file} to {dst_file}: {e}', exc_info=True)

def main():
    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description='Integrate Sorted Photos')
    parser.add_argument('SortedFolder', nargs='?', default='I:/NeRoztříděno', help='Path to the sorted folder')
    parser.add_argument('TargetFolder', nargs='?', default='J:/FotoTest', help='Path to the target folder')
    parser.add_argument('LogFile', nargs='?', default=f'H:/Logs/IntegrateSortedPhotosLog.{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log', help='Path to the log file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode to log to console')

    args = parser.parse_args()

    # Set up logging to the specified log file
    setup_logging(args.LogFile, args.debug)

    # Verify the log file creation
    if os.path.exists(args.LogFile):
        logging.debug(f'Log file created: {args.LogFile}')
    else:
        logging.error(f'Failed to create log file: {args.LogFile}')

    # Log the parsed arguments
    logging.debug(f'Parsed arguments: SortedFolder={args.SortedFolder}, TargetFolder={args.TargetFolder}, LogFile={args.LogFile}, Debug={args.debug}')

    # Ensure the folders and log file path are correct
    sorted_folder = args.SortedFolder
    target_folder = args.TargetFolder

    # Log the folders and log file path
    logging.debug(f'Sorted folder: {sorted_folder}')
    logging.debug(f'Target folder: {target_folder}')

    # Log before calling the file copying functionality
    logging.debug('Starting to copy files with metadata.')

    # Implement the file copying functionality
    copy_files_with_metadata(sorted_folder, target_folder)

    # Log after completing the file copying functionality
    logging.debug('Completed copying files with metadata.')

if __name__ == '__main__':
    main()