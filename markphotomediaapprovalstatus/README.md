# Mark Photo Media Approval Status

This Python tool allows manual evaluation of photo statuses in a CSV database for each defined photobank. It displays information about the photo/video/vector, shows the media content, and provides a graphical user interface for approving or rejecting media files. The results are saved back to the CSV and to a log.

## Project Structure

```
markphotomediaapprovalstatus/
│
├── markphotomediaapprovalstatus.py              # Main executable script
│
├── shared/                                      # Contains only general (reusable) functions
│   ├── file_operations.py                       # File operations functions
│   ├── utils.py                                 # Utility functions
│   └── logging_config.py                        # Logging configuration
│
├── markphotomediaapprovalstatuslib/             # Specific functions and constants for this script
│   ├── constants.py                             # Script-specific constants
│   ├── status_handler.py                        # Status filtering and processing
│   └── gui_handler.py                           # Graphical user interface for media review
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

- `--csv_path`: Path to the CSV file with photo media data (default: "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv")
- `--log_dir`: Directory for log files (default: "H:/Logs")
- `--debug`: Enable debug logging

## Functionality

1. Loads a CSV file containing media records
2. Finds records where at least one status column has the value "kontrolováno"
3. For each defined photobank:
   - Goes through the filtered records
   - If a record has "kontrolováno" status for the current bank:
     - Displays information about the record
     - Loads and displays the media file from the path specified in the "Cesta" column
     - Presents a GUI for the user to make a decision
     - Writes the answer back to the column
     - Logs the result (filename + bank + result)
4. If any changes were made:
   - Backs up the original CSV (copy with timestamp)
   - Writes the updated CSV back to the original path

## User Interaction

The application provides a graphical user interface for reviewing media files:

1. For each photobank, a window is displayed showing:
   - Information about the current media file (filename, title, description, keywords)
   - The actual media content loaded from the path specified in the "Cesta" column
   - Radio buttons for selecting a decision

2. For images and vector graphics:
   - The image is displayed in the center of the window

3. For videos:
   - A video player is shown with playback controls
   - Buttons for play/pause, stop, rewind, and forward

4. Decision options:
   - Radio buttons for selecting the decision:
     - **Approve (a)**: Mark the media as approved ("schváleno")
     - **Reject (n)**: Mark the media as rejected ("zamítnuto")
     - **Maybe (m)**: Mark the media with uncertain status ("schváleno?")
     - **Skip (s)**: Skip the current media without changing its status
   - **Save Decision** button to confirm your choice and move to the next item

5. Keyboard shortcuts:
   - **A**: Select Approve option
   - **N**: Select Reject option
   - **M**: Select Maybe option
   - **S**: Select Skip option

The application processes all media files for one photobank before moving to the next one.

6. Window behavior:
   - If you close the window using the X button, the entire application will exit
   - After processing all entries for a bank, the window will close automatically and the next bank's window will open
   - Changes are saved after each bank is processed, ensuring no progress is lost
