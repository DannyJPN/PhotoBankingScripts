# markphotomediaapprovalstatus - Version 2.0

## Status: FUNCTIONAL ✅

**Last Updated:** 2025-12-31

---

## 🚨 BREAKING CHANGES IN v2.0

**Iteration Order Changed:** This version implements **bank-first iteration** as originally specified in README.md.

**Old Behavior (v1.0):**
- ❌ Iterated FILES → showed ALL banks for each file
- One GUI window per file, 2-column grid with all banks

**New Behavior (v2.0):**
- ✅ Iterates BANKS → shows all files for each bank
- One GUI window per file per bank, single bank controls
- Matches original README specification

**Why This Change:**
- Fixes issue #70: Iteration order mismatch
- Aligns with documented workflow
- Provides focused, bank-by-bank review process

---

## What's Working

### Core Functionality
- ✅ **GUI-based approval workflow** - Interactive media viewer with approval controls
- ✅ **Bank-first iteration** - Processes one photobank at a time, then all files for that bank
- ✅ **Sequential file processing** - Processes files one by one with immediate saving
- ✅ **Single-bank mode** - Shows controls for one bank only (focused workflow)
- ✅ **Media display** - Shows images and video files with responsive sizing
- ✅ **Progressive saving** - Saves changes after each file to prevent data loss

### GUI Features
- ✅ **Single-bank focused layout** - Shows one bank at a time for focused review
- ✅ **File path display** - Bold, prominent filename display
- ✅ **Media information** - Shows title and description metadata
- ✅ **Radiobutton controls** - Simple approval options: Žádný, Schváleno, Zamítnuto, Schváleno?
- ✅ **Mouse wheel scrolling** - Easy navigation through controls
- ✅ **Window centering** - Automatically centers on screen

### Data Processing
- ✅ **CSV integration** - Reads and updates PhotoMedia.csv
- ✅ **Centralized file operations** - Uses shared/file_operations.py
- ✅ **Backup creation** - Creates backups when saving changes
- ✅ **Status filtering** - Only processes files with "kontrolováno" status
- ✅ **Graceful exit handling** - Ctrl+C equivalent on window close

---

## Architecture

### File Structure
```
markphotomediaapprovalstatus/
├── markphotomediaapprovalstatus.py      # Main script
├── markphotomediaapprovalstatuslib/
│   ├── constants.py                     # Configuration constants
│   ├── media_helper.py                  # Media processing logic
│   ├── media_viewer.py                  # GUI implementation
│   └── status_handler.py                # Status filtering utilities
└── shared/                              # Common utilities
```

### Key Components
- **MediaViewer**: tkinter-based GUI with PanedWindow layout
- **process_approval_records**: Sequential processing with progressive saving
- **Centralized logging**: All operations logged for audit trail

---

## Usage

```bash
python markphotomediaapprovalstatus.py [--csv_path PATH] [--log_dir DIR] [--debug]
```

### Workflow (v2.0 - Bank-First)
1. Script loads PhotoMedia.csv and filters for "kontrolováno" status
2. **FOR EACH PHOTOBANK** (outer loop):
   - Filter files with "kontrolováno" for this bank
   - **FOR EACH FILE** (inner loop):
     - GUI opens showing file with single bank approval controls
     - User selects approval status for this bank only
     - Changes saved immediately after each file
3. Process moves to next photobank after completing all files
4. Window closes automatically after processing all banks

---

## Technical Notes

### Dependencies
- tkinter (GUI framework)
- PIL/Pillow (image processing)
- pygame (video playback support)
- Standard CSV processing libraries

### Performance
- **Memory efficient**: Loads one image at a time
- **Responsive**: Image scaling maintains aspect ratios
- **Safe**: Progressive saving prevents data loss

### Configuration
- Default CSV path: `L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv`
- Supported formats: Images (JPG, PNG, etc.), Videos (MP4, AVI, etc.)
- Banks processed: All 10 configured photobanks

---

## Version History

### v2.0 (2025-12-31) 🚨 BREAKING CHANGES
- **Bank-first iteration**: Changed from file-first to bank-first processing order
- **Single-bank UI**: Shows one bank at a time instead of all banks in 2-column grid
- **Focused workflow**: Process all files for one bank before moving to next bank
- Added `filter_records_by_bank_status()` for bank-specific filtering
- Refactored `process_approval_records()` with outer loop for banks, inner loop for files
- Modified `show_media_viewer()` and `load_media()` to accept `target_bank` parameter
- Updated `MediaViewer.process_current_file()` to return single decision for bank-first mode
- Fixes issue #70: Iteration order mismatch with README specification

### v1.0 (2025-01-24)
- Initial functional release
- Complete GUI implementation following sortunsortedmedia patterns
- Simplified radiobutton-only interface (removed rejection reasons system)
- Progressive saving and centralized file operations
- Two-column layout with responsive design

---

## Future Enhancements

### Potential Improvements
- Keyboard shortcuts for faster operation
- Batch selection modes
- Undo functionality
- Enhanced video playback controls
- Statistics dashboard

### Known Limitations
- Video playback is basic (preview only)
- No bulk operations support
- Sequential processing only (no parallel mode)

---

*This script is part of the PhotoBanking pipeline - handles approval status marking for media files across multiple photobank platforms.*