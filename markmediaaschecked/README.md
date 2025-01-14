# MarkMediaAsChecked

MarkMediaAsChecked is a Python script designed to automate the process of marking media files as checked within a CSV file. The script performs three main functions: loading a CSV file, marking certain rows as checked based on specific criteria, and saving the updated CSV file while creating a backup. The script uses the logging module to create a log file with dynamically generated filenames based on the script name and current date/time, with color-coded log levels. Additionally, it displays a command-line progress bar during CSV processing.

## Overview

The project is structured to separate the main script logic from utility functions and constants. It is organized into two primary folders: `markmediaascheckedlib` for script-specific functions and `shared` for reusable components. The main script, `mark_media_as_checked.py`, handles argument parsing and orchestrates the CSV processing workflow. Key technologies used in the project include:

- **Python**: The primary programming language.
- **pandas**: For data manipulation and analysis.
- **colorlog**: For colored logging.
- **tqdm**: For displaying progress bars.

### Project Structure

```
MarkMediaAsChecked/
├── mark_media_as_checked.py
├── markmediaascheckedlib/
│   ├── constants.py
│   ├── csv_handler.py
│   ├── mark_files.py
├── shared/
│   ├── logging_config.py
│   ├── log_colors.json
│   ├── utils.py
└── README.md
```

## Features

- **Load CSV**: Reads a CSV file and loads its content into a data structure for processing.
- **Mark Files as Checked**: Iterates through the CSV content and updates the status of media files.
- **Save CSV**: Saves the updated CSV content back to the original file, creating a backup of the original file.
- **Logging**: Generates log files with color-coded log levels and dynamically generated filenames.
- **Progress Bar**: Displays a command-line progress bar during CSV processing.

## Getting Started

### Requirements

- Python 3.x
- pandas
- colorlog
- tqdm

### Quickstart

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd MarkMediaAsChecked
    ```

2. **Install the required libraries**:
    ```sh
    pip install pandas colorlog tqdm
    ```

3. **Run the script**:
    ```sh
    python mark_media_as_checked.py --PhotoCsvFile="path/to/your/csvfile.csv" --LogFile="path/to/log/directory" --debug
    ```

### License

The project is proprietary (not open source). 

```
Copyright (c) 2024.
```