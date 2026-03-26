# markphotomediaapprovalstatus - Version 2.0

## Status: FUNCTIONAL

**Last Updated:** 2026-03-26

---

## What's Working

### Core Functionality
- GUI-based approval workflow
- Bank-first iteration
- Sequential file processing
- Single-bank mode
- Media display for images and videos
- Progressive saving

### Data Processing
- CSV integration
- Centralized file operations
- Backup creation
- Status filtering for `kontrolováno`

---

## Architecture

### File Structure
```
markphotomediaapprovalstatus/
+-- markphotomediaapprovalstatus.py
+-- markphotomediaapprovalstatuslib/
|   +-- constants.py
|   +-- media_helper.py
|   +-- media_viewer.py
|   +-- status_handler.py
+-- shared/
```

### Key Components
- `MediaViewer`: GUI implementation
- `process_approval_records`: Sequential GUI processing with saving
- Centralized logging via shared utilities

---

## Usage

```bash
python markphotomediaapprovalstatus.py [--csv_path PATH] [--log_dir DIR] [--debug]
```

### Workflow
1. Script loads `PhotoMedia.csv` and filters for `kontrolováno`
2. For each photobank:
   - Filter files with `kontrolováno` for this bank
   - For each file:
     - GUI opens with single-bank controls
     - User selects approval status
     - Changes are saved during processing

---

## Technical Notes

### Dependencies
- tkinter / PyQt5 GUI dependencies used by the existing script
- PIL/Pillow and related media support from the current environment
- Standard CSV processing libraries

### Configuration
- Default CSV path is stored in constants
- Supported formats include images and videos already handled by the viewer

---

## Version History

### v2.0
- Bank-first iteration
- Single-bank UI
- Focused workflow per bank

### v1.0
- Initial functional release
