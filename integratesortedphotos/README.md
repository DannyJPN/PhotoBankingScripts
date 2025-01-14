# IntegrateSortedPhotos

IntegrateSortedPhotos is a command-line tool written in Python designed to copy files from a sorted folder to a target folder while preserving their original creation dates. The tool logs the operations to a specified log file, providing detailed information about the process.

## Overview

IntegrateSortedPhotos follows a modular architecture, with the main script handling argument parsing and invoking functions from separate modules. This design ensures maintainability and scalability by separating concerns and organizing code logically. The project uses Python's standard libraries for file operations and logging, along with the colorlog library for color-coded log messages.

### Technologies Used
- **Python**: The primary programming language for the project.
- **shutil**: Standard library for high-level file operations.
- **logging**: Standard library for logging.
- **colorlog**: Library for color-coded log messages.

### Project Structure
```
IntegrateSortedPhotos/
├── integrate_sorted_photos.py          # Main script
├── integratesortedphotoslib/           # Library specific to this script
│   ├── argument_parser.py              # Argument parsing logic
│   ├── constants.py                    # Constants used in the project
│   ├── images_extensions.py            # Supported image file extensions
│   ├── illustrations_extensions.py     # Supported illustration file extensions
│   ├── videos_extensions.py            # Supported video file extensions
├── shared/                             # Shared library for potential reuse
│   ├── logging_config.py               # Logging configuration setup
│   ├── log_colors.json                 # Color configuration for logging
├── README.md                           # Project documentation
```

## Features

- **File Copying**: Copies files from a sorted folder to a target folder, preserving the original creation dates.
- **Logging**: Logs detailed information about the process, including debug information if enabled.
- **Modular Design**: Organized code with separate modules for argument parsing, logging configuration, and file extension handling.

## Getting Started

### Requirements

Before you begin, ensure you have the following installed on your machine:
- Python 3.6 or higher
- colorlog library (install via `pip install colorlog`)

### Quickstart

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/IntegrateSortedPhotos.git
    cd IntegrateSortedPhotos
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Run the script**:
    ```sh
    python integrate_sorted_photos.py [SortedFolder] [TargetFolder] [LogFile] [--debug]
    ```
    - `SortedFolder` (optional): Path to the sorted folder. Default is `I:/Roztříděno`.
    - `TargetFolder` (optional): Path to the target folder. Default is `J:/`.
    - `LogFile` (optional): Path to the log file. Default is `H:/Logs/integrate_sorted_photos_log.log`.
    - `--debug` (optional): Enable debug mode for detailed logging.

    **Example**:
    ```sh
    python integrate_sorted_photos.py "C:/Photos/Sorted" "D:/Photos/Target" "C:/Logs/photos_log.log" --debug
    ```

### License

The project is proprietary (not open source). 

```
Copyright (c) 2024.
```