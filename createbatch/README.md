```markdown
# CreateBatch

CreateBatch is a Python-based script designed to streamline the processing of media files based on a CSV input. The script ensures necessary directories exist, loads and parses a CSV file, filters media items based on specific criteria, copies these items to a designated folder, and updates their EXIF data. Additionally, it prepares calls to other placeholder Python scripts for further processing, features colorful console logging, and supports a debug mode for non-error logging.

## Overview

CreateBatch is architected to separate its main logic from specific functionalities, promoting modularity and reuse. The main script contains only the `main` method, while all other functions are encapsulated in separate files within the `createbatchlib` and `shared` folders. The `createbatchlib` folder houses functions specific to this script, whereas the `shared` folder contains methods with potential for reuse in other scripts. The project leverages the following technologies:

- **Python**: The core programming language for the script.
- **pandas**: For data manipulation and analysis, specifically handling CSV files.
- **tqdm**: To display progress bars in the command line.
- **colorlog**: For colorful logging in the command line.
- **Pillow**: For handling image files and updating EXIF data.
- **exif**: For reading and writing EXIF data in image files.

### Project Structure

- `README.md`: Comprehensive overview of the CreateBatch project.
- `create_batch.py`: Main script containing the `main` method.
- `createbatchlib/`: Folder containing files with functions specific to this script.
  - `constants.py`: Defines constants used throughout the project.
  - `copy_media_items_to_batch.py`: Copies media items to the specified folder.
  - `ensure_directories.py`: Ensures necessary directories exist.
  - `get_prepared_media_items.py`: Filters media items based on specific criteria.
  - `illustration_extensions.py`: Defines supported illustration file extensions.
  - `illustration_extensions.txt`: List of illustration file extensions.
  - `image_extensions.py`: Defines supported image file extensions.
  - `image_extensions.txt`: List of image file extensions.
  - `load_csv.py`: Loads and parses the CSV file.
  - `update_exif_data.py`: Updates EXIF data of media files.
  - `video_extensions.py`: Defines supported video file extensions.
  - `video_extensions.txt`: List of video file extensions.
- `shared/`: Folder containing shared methods.
  - `log_colors.json`: JSON configuration for log colors.
  - `logging_config.py`: Sets up the logging configuration.
- `export_prepared_media.py`: Placeholder script for exporting prepared media.
- `launch_photobanks.py`: Placeholder script for launching photobanks.
- `mark_media_as_checked.py`: Placeholder script for marking media as checked.

## Features

- **Directory Management**: Ensures necessary directories exist before processing.
- **CSV Handling**: Loads and parses the CSV file to extract media items.
- **Media Item Filtering**: Filters media items based on specific criteria.
- **File Copying**: Copies media items to a designated folder, ensuring no duplicates.
- **EXIF Data Update**: Updates EXIF data of media files with specified metadata.
- **Progress Bars**: Displays progress bars for file copying and EXIF data updating.
- **Colorful Logging**: Features colorful console logging for better readability.
- **Debug Mode**: Supports a debug mode for detailed logging.

## Getting started

### Requirements

To run the CreateBatch project, ensure you have the following installed:

- Python 3.x
- pandas
- tqdm
- colorlog
- Pillow
- exif

### Quickstart

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd CreateBatch
    ```

2. **Install dependencies**:
    ```sh
    pip install pandas tqdm colorlog Pillow exif
    ```

3. **Run the script**:
    ```sh
    python create_batch.py --PhotoCsvFile="path/to/PhotoMediaTest.csv" --ProcessedMediaFolder="path/to/PhotoBankMediaTest" --Debug=True
    ```

### License

The project is proprietary. 

```
Copyright (c) 2024.
```
```