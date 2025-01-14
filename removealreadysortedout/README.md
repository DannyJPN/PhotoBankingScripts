# RemoveAlreadySortedOut

RemoveAlreadySortedOut is a Python script designed to organize and deduplicate files from an unsorted folder to a target folder. The script unifies files from subdirectories into a single directory, retrieves file paths, finds already sorted files by comparing filenames, and removes sorted files by comparing file sizes and MD5 hashes. The script supports detailed logging with color-coded output for different log levels.

## Overview

The project is structured to separate the main script from its functions, which are organized into specific modules. The script uses the built-in logging module for detailed logging, with color-coded output provided by the `colorlog` package. The project utilizes the `Pillow` library for image handling.

### Technologies Used

- **Python**: The core programming language used to implement the script.
- **colorlog**: A Python package for colored logging output.
- **Pillow**: A Python Imaging Library (PIL) fork for opening, manipulating, and saving many different image file formats.

### Project Structure

The project consists of the following files and directories:

- `remove_already_sorted_out.py`: The main script that manages and logs the process of sorting files from an unsorted folder to a target folder.
- `removealreadysortedoutlib/`: Directory containing script-specific modules.
  - `constants.py`: Contains constants used in the script.
  - `display_files.py`: Handles displaying files side-by-side.
  - `find_already_sorted_files.py`: Finds already sorted files.
  - `get_file_paths.py`: Retrieves file paths from a directory recursively.
  - `md5.py`: Calculates MD5 hashes for files.
  - `remove_sorted_files.py`: Removes sorted files.
  - `rename_files.py`: Renames files according to specified rules.
  - `unify_files.py`: Unifies files from subdirectories into a single directory.
  - `supported_extensions_images.txt`: List of supported image file extensions.
  - `supported_extensions_videos.txt`: List of supported video file extensions.
  - `supported_extensions_illustrations.txt`: List of supported illustration file extensions.
- `shared/`: Directory containing shared modules.
  - `logging_config.py`: Sets up logging configuration.
  - `log_colors.json`: Defines colors for different log levels.
  - `utils.py`: Utility functions, including log filename generation.

## Features

- **Unify Files**: Moves all files from subdirectories to the main directory, ensuring no duplicates in the main directory.
- **Retrieve File Paths**: Lists all file paths in a directory recursively.
- **Find Already Sorted Files**: Identifies files in the target folder that have the same name as files in the unsorted folder.
- **Remove Sorted Files**: Compares file sizes and MD5 hashes to determine and remove duplicate files, with user interaction for ambiguous cases.
- **Detailed Logging**: Logs all operations with color-coded output for different log levels.

## Getting Started

### Requirements

- **Python**: Ensure Python is installed on your system.
- **colorlog**: Install the colorlog package.
- **Pillow**: Install the Pillow package.

### Quickstart

1. **Clone the repository** (if applicable):

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install the required packages**:

   ```bash
   pip install colorlog Pillow
   ```

3. **Run the script**:

   ```bash
   python remove_already_sorted_out.py --unsorted-folder <path-to-unsorted-folder> --target-folder <path-to-target-folder> --log-file <path-to-log-file> --debug
   ```

   - `--unsorted-folder`: Path to the unsorted folder (default: `I:/Neroztříděno`).
   - `--target-folder`: Path to the target folder (default: `I:/Roztříděno`).
   - `--log-file`: Path to the log file (default: dynamically generated based on script name and current date/time).
   - `--debug`: Enable debug level logging (optional).

### Testing Instructions

1. **Prepare the environment**:
   - Create a test directory structure with subdirectories and files.

2. **Run the script**:
   - Execute the script with the appropriate parameters.

3. **Verify the results**:
   - Check the main directory to ensure files from subdirectories are moved without duplication.
   - Ensure that if a file already exists in the main directory, the duplicate in the subdirectory is removed.

4. **Check logs**:
   - Check the terminal output for logs indicating the unification of files in the `I:/NeroztříděnoTest` directory.
   - Ensure that logs indicate files are being moved from subdirectories to the main directory, along with a progress bar.
   - Ensure that if a file already exists in the main directory, the duplicate in the subdirectory is removed instead of being renamed.

### License

The project is proprietary (not open source).

```
© 2024 RemoveAlreadySortedOut
```