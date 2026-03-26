# Mark Photo Media Approval Status

This Python tool allows manual evaluation of photo statuses in a CSV database for each defined photobank. It displays information about the photo/video/vector, shows the media content, and provides a graphical user interface for approving or rejecting media files. The results are saved back to the CSV and to a log.

## Project Structure

```
markphotomediaapprovalstatus/
|
+-- markphotomediaapprovalstatus.py              # Main executable script
|
+-- shared/                                      # Contains only general (reusable) functions
|   +-- file_operations.py                       # File operations functions
|   +-- utils.py                                 # Utility functions
|   +-- logging_config.py                        # Logging configuration
|
+-- markphotomediaapprovalstatuslib/             # Specific functions and constants for this script
|   +-- constants.py                             # Script-specific constants
|   +-- status_handler.py                        # Status filtering and processing
|   +-- media_viewer.py                          # Graphical user interface for media review
|   +-- media_helper.py                          # Approval processing flow
```

## Installation

Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

```
python markphotomediaapprovalstatus.py [--csv_path CSV_PATH] [--log_dir LOG_DIR] [--debug]
```

### Arguments

- `--csv_path`: Path to the CSV file with photo media data
- `--log_dir`: Directory for log files
- `--debug`: Enable debug logging
- `--include-edited`: Include edited photos from `upravené` folders

## Functionality

1. Loads a CSV file containing media records
2. Finds records where at least one status column has the value `kontrolováno`
3. For each defined photobank:
   - Goes through the filtered records
   - If a record has `kontrolováno` status for the current bank:
     - Displays information about the record
     - Loads and displays the media file from the path specified in the `Cesta` column
     - Presents a GUI for the user to make a decision
     - Writes the answer back to the column
     - Logs the result
4. If any changes were made:
   - Backs up the original CSV
   - Writes the updated CSV back to the original path

## User Interaction

The application provides a graphical user interface for reviewing media files:

1. For each photobank, a window is displayed showing:
   - Information about the current media file
   - The actual media content loaded from the path specified in the `Cesta` column
   - Radio buttons for selecting a decision

2. For images and vector graphics:
   - The image is displayed in the center of the window

3. For videos:
   - A video player is shown with playback controls

4. Decision options:
   - **Approve (a)**: Mark the media as approved (`schváleno`)
   - **Reject (n)**: Mark the media as rejected (`zamítnuto`)
   - **Maybe (m)**: Mark the media with uncertain status (`schváleno?`)
   - **Skip (s)**: Skip the current media without changing its status

5. Keyboard shortcuts:
   - **A**: Select Approve option
   - **N**: Select Reject option
   - **M**: Select Maybe option
   - **S**: Select Skip option

6. Window behavior:
   - Closing the window exits the whole application
   - After processing all entries for a bank, the window closes automatically and the next bank opens
   - Changes are saved during processing so progress is not lost
