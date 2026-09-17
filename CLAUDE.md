# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 📄 Photobanking – Global Rules & Architecture

## Scope

These rules apply to **all scripts for photobanks** in this repository.
They are **shared** across all modules; local specifics may be added at script level.

---

## Project structure

* Every photobank script folder must contain:

  * `[script_name]lib/` with `constants.py` (default paths, headers, encodings). 
    Example: `sortunsortedmedia/` → `sortunsortedmedialib/`, `createbatch/` → `createbatchlib/`
  * `shared/` (common helpers, logging).
  * `tests/` (with `unit/`, `integration/`, `performance/`, `security/`).
* **Main scripts**: only top-level `.py` files beside `[script_name]lib/` or `shared/` may be directly executable. Files inside libraries are not executables.
* **Outputs**:

  * Always under result folder defined in `constants.py` (overridable by CLI arg).
  * Folder structure and filenames must follow fixed convention (`<BankName>Output.csv/json`).
  * **Exception for batch splitting:** Banks with batch size limits create numbered files:
    - Example: `GettyImagesOutput_1.csv`, `GettyImagesOutput_2.csv`
    - Each file contains maximum items per bank's batch size limit
    - Subfolder structure: `GettyImages/batch_001/`, `GettyImages/batch_002/`
  * No other naming variations allowed.

---

## Language & style

* **Python 3.12** only.
* Always run in **venv**, pip installs allowed only inside venv.
* **Black** (line length 120) and **Ruff** required.
* Type hints everywhere.
* Imports explicit, no wildcards.
* Docstrings mandatory, **Sphinx style**.
* **Code comments** must be in **English**.
* **Comments only for functions and classes** (for documentation generators). No inline comments after every line.

---

## Logging

* Only the **shared logger** is allowed (Colorlog, settings from `constants.py`).
* Logs always in **English**.
* Input files (media) must **never be modified**.
* On corrupted/unsupported media → **log error** (what, where, why) but continue safely.

---

## Errors

* Normal flow: raise exceptions.
* Fatal: `sys.exit(1)` at main level.
* Never silent failures.

---

## Dates & encodings

* CSV headers and encodings are fixed per photobank (see each `constants.py`).
* Metadata dates may appear in arbitrary format; parser must log issues, not crash.
* Empty or malformed dates are allowed → log warning.

---

## Tests

* **Every function** must be tested, including error paths.
* Tests mirror folder structure; names: `test_<unit>__<function>__<intent>()`.
* **Timeouts**:

  * Unit ≤ 10 min
  * Others ≤ 24 h (shorter if possible).
* Test logs go into dedicated test-log folder (path in `constants-test.py`).
* Commit blocked if tests fail or break existing ones.

---

## Git workflow

* Claude-only branches: `claude/<type>/<action>` (e.g., `claude/feature/upload`).

  * On these: Claude may commit/push/pull freely.
* On any user branch: write actions only after explicit approval.
* Claude must **never merge** automatically.
* Commits: short, precise.
* One branch/PR = one feature.
* PR requires owner review, no auto-merge.

### Multi-line Commit Messages

For detailed commit messages, use one of these approaches:

1. **File-based (recommended)**: Create temporary file and use `git commit -F filename`
2. **Multiple -m flags**: `git commit -m "Title" -m "Line 1" -m "Line 2"`  
3. **$'...' syntax**: `git commit -m $'Title\n\nDescription\nMore details'`
4. **Printf with variable**: `MSG="$(printf "line1\nline2")" && git commit -m "$MSG"`

File-based approach avoids shell escaping issues and supports full formatting.

### Commit Best Practices

**Before committing:**
1. **Stop Dropbox**: Check if Dropbox is running and kill it before git operations

   **On Windows (use PowerShell via Bash tool):**
   - Check: `powershell.exe -Command "Get-Process | Where-Object {\\$_.Name -like '*Dropbox*'}"`
   - Kill: `powershell.exe -Command "Stop-Process -Name 'Dropbox' -Force"`
   - **Note**: Always use `powershell.exe -Command` when calling PowerShell from Bash tool

   **On Linux/macOS (use bash):**
   - Check: `ps aux | grep -i dropbox`
   - Kill: `pkill -9 dropbox`

   - **Critical**: Git operations fail with "Permission denied" errors when Dropbox is syncing
   - **Platform detection**: Check `platform` in <env> (win32 = Windows, linux = Linux, darwin = macOS)

2. **Clean up temporary files**: Always remove `*.tmp.*` files before staging
3. **Stage only modified files**: Never use `git add .` - explicitly list only the files you modified
4. **Example**: `git add file1.py file2.py constants.py` (not `git add .`)

**After pushing:**

**On Windows (PowerShell):**
- **Restart Dropbox**: `Start-Process "C:\Program Files (x86)\Dropbox\Client\Dropbox.exe"`

**On Linux/macOS (bash):**
- **Restart Dropbox**: `dropbox start` or check system-specific command

**Rationale**:
- Dropbox file locking prevents Git from writing to `.git/objects/`
- Prevents accidental commits of temporary files, build artifacts, or unrelated changes
- PowerShell must be used on Windows for proper process management

---

## File Operations

* **Centralized CRUD**: All file operations (Create, Read, Update, Delete) must go through `shared/file_operations.py`
* **No direct file manipulation**: Scripts must NOT use `shutil`, `os.makedirs`, direct file I/O outside of `file_operations`
* **Standard functions**: Use `copy_file()`, `ensure_directory()`, `delete_file()`, etc. from `file_operations`
* **Consistency**: This ensures uniform error handling, logging, and metadata preservation across all scripts

---

## Secrets

* API keys & credentials: only via env or special local files with **templates** in repo.
* Such files must never reach Git.
* `constants-test.py` provides test-only values.

---

## Implementation status

Claude must maintain a dedicated status file (e.g., `IMPLEMENTATION_STATUS.md`) in each script folder:

* Updated **with every meaningful change**.
* Must contain: what is implemented, what is pending, known limitations.
* Acts as the single source of truth for progress tracking.

---

## References

* **Python**: docs.python.org, PyPI, pip docs.
* **Libraries**: NumPy, Pandas, Pillow, OpenCV, ImageIO, ExifTool, FFmpeg, libvips, ImageMagick.
* **Photobanks**:
  * **Active**: ShutterStock, AdobeStock, Dreamstime, DepositPhotos, GettyImages, Pond5, Alamy, 123RF, Pixta, Freepik, Vecteezy, StoryBlocks, Envato, 500px, MostPhotos
  * **Deprecated**: BigStockPhoto, CanStockPhoto
* **AI providers**: OpenAI, Anthropic, Google AI, Mistral, Meta (Llama), Hugging Face.
* **Protocols**: FTP (RFC 959), FTPS (RFC 4217), SFTP (RFC 4253/4254).

---

# 🏗️ Independent Script Pipeline Architecture

## Complete Pipeline Overview

The Fotobanking system consists of **10 independent, standalone scripts** that form a complete processing pipeline from raw media to photobank submission:

```
Raw Media → Sort → Create → AI Meta → Export → Mark → Remove → Update → Launch → Upload
     ↓        ↓       ↓        ↓        ↓       ↓       ↓        ↓       ↓        ↓
  [sort]  [create] [give]  [export]  [mark] [remove] [update] [launch] [upload] [integrate]
  Script   Script  Script   Script   Script  Script   Script   Script   Script    Script
```

## Independent Script Modules

### 1. `sortunsortedmedia/` - Media Organization Script
**Standalone executable:** `sortunsortedmedia.py`, `sortunsortedmediafile.py`  
**Purpose:** Organize raw media into structured date/category hierarchy  
**Input:** Unsorted media files from specified directories  
**Output:** Organized folder structure by date/category/camera  

### 2. `createbatch/` - Batch Creation Script  
**Standalone executable:** `createbatch.py`  
**Purpose:** Group organized media into processing batches  
**Input:** Structured media folders (from sortunsortedmedia)  
**Output:** Batched media groups for metadata processing  

### 3. `givephotobankreadymediafiles/` - AI Metadata Generation Script
**Standalone executable:** `givephotobankreadymediafiles.py`, `preparemediafile.py`  
**Purpose:** Generate AI-powered metadata (titles, descriptions, keywords)  
**Input:** Media files (individual or batched)  
**Output:** Enhanced PhotoMedia.csv with complete metadata  

### 4. `exportpreparedmedia/` - Bank Export Script
**Standalone executable:** `exportpreparedmedia.py`  
**Purpose:** Convert metadata to bank-specific export formats  
**Input:** PhotoMedia.csv with completed metadata  
**Output:** Bank-specific CSV/JSON files ready for upload  

### 5. `markmediaaschecked/` - Status Tracking Script
**Standalone executable:** `markmediaaschecked.py`  
**Purpose:** Mark processed files to avoid reprocessing  
**Input:** Processed media files  
**Output:** Updated status in PhotoMedia.csv  

### 6. `removealreadysortedout/` - Duplicate Management Script
**Standalone executable:** `remove_already_sorted_out.py`  
**Purpose:** Remove duplicates and already-processed files from workflow  
**Input:** Media directories and processing databases  
**Output:** Cleaned media sets without duplicates  

### 7. `updatemediadatabase/` - Database Synchronization Script
**Standalone executable:** `updatemediadatabase.py`  
**Purpose:** Synchronize metadata database with file system changes  
**Input:** PhotoMedia.csv and file system state  
**Output:** Updated and synchronized database  

### 8. `launchphotobanks/` - Submission Portal Script
**Standalone executable:** `launch_photo_banks.py`  
**Purpose:** Open photobank submission portals in browser  
**Input:** Bank configuration and export files  
**Output:** Launched browser sessions for manual upload  

### 9. `uploadtophotobanks/` - Automated Upload Script
**Standalone executable:** `uploadtophotobanks.py` (planned)  
**Purpose:** Automated upload to photobank APIs/FTP servers  
**Input:** Bank-specific export files and credentials  
**Output:** Uploaded media with submission confirmations  

### 10. `integratesortedphotos/` - Library Integration Script
**Standalone executable:** `integrate_sorted_photos.py`  
**Purpose:** Merge sorted photos into main library structure  
**Input:** Sorted photo directories  
**Output:** Integrated main photo library


