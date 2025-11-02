# SortUnsortedMedia

A Python tool for organizing and sorting media files (photos and videos) into a structured directory hierarchy.

## Features

- Automatically detects camera type from filename patterns
- Extracts creation dates from EXIF metadata
- Identifies edited files based on filename patterns
- Organizes files into a structured folder hierarchy by date and category
- Interactive categorization with media preview
- Supports both batch processing and single file processing

## Requirements

- Python 3.6+
- ExifTool (automatically downloaded on Windows, manual installation required on Linux/Mac)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/sortunsortedmedia.git
   cd sortunsortedmedia
   ```

2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. On Linux/Mac, install ExifTool:
   - Ubuntu/Debian: `sudo apt-get install exiftool`
   - macOS: `brew install exiftool`
   - On Windows, ExifTool will be automatically downloaded

## Usage

### Processing all unsorted media

```
python sortunsortedmedia.py --unsorted_folder "path/to/unsorted" --target_folder "path/to/sorted"
```

Options:
- `--unsorted_folder`: Folder containing unsorted media files (default: "I:/Neroztříděno")
- `--target_folder`: Target folder for sorted media (default: "I:/Roztříděno")
- `--interval`: Interval in seconds to wait between processing files (default: 3600)
- `--debug`: Enable debug logging

### Processing a single media file

```
python sortunsortedmediafile.py --media_file "path/to/file.jpg" --target_folder "path/to/sorted"
```

Options:
- `--media_file`: Path to the media file to process (required)
- `--target_folder`: Target folder for sorted media (default: "I:/Roztříděno")
- `--interval`: Interval in seconds to wait after processing (default: 60)
- `--log_file`: Path to log file (default: auto-generated)
- `--debug`: Enable debug logging

## Output Structure

The tool organizes files into the following structure:

- Photos: `{target_folder}/{year}/{month}/{date}_{category}_{camera}.jpg`
- Videos: `{target_folder}/Video/{year}/{month}/{date}_{category}_{camera}.mp4`
- Edited: `{target_folder}/Upravené/{year}/{month}/{date}_{category}_{camera}_{edit_type}.jpg`

## Customization

You can customize the behavior by modifying the constants in `sortunsortedmedialib/constants.py`:

- `DEFAULT_CATEGORIES`: List of predefined categories
- `CAMERA_REGEXES`: Regular expressions for detecting camera models
- `EDITED_TAGS`: Tags indicating edited files
- `EXTENSION_TYPES`: File extensions and their media types
- `FOLDER_STRUCTURE`: Format strings for folder structure
