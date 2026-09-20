# PullNewMediaToUnsorted Implementation Status

Last updated: 2026-09-20

## Implemented
- Pulling new media from the configured sources into the unsorted folder, flattening and deduplicating by content hash.
- Dated filename format `<prefix><YYYYMMDD>_<XXXX>.<ext>` (e.g. `NIK_20260612_8888.JPG`), replacing the sequential counter with its 999 999 ceiling.
  - The date is the oldest available EXIF/file date (`get_best_creation_date`). It is an output for the user and the file system that keeps the name unique without a variable length; the scripts never read it back. The 4-digit camera sequence number is kept from the original name.
  - `normalize_indexed_filenames` is idempotent: an already-dated file is never renamed again, and a hash match against the reference folder reuses the reference's canonical name.
  - All name comparisons are case-insensitive (Windows/NTFS semantics, `name_key`).
  - A name collision with a file of identical content (same hash) is a duplicate copy, not a conflict: the name is kept and no suffix is added. A collision with different content gets `_B`, `_C`, ... and names stay unique across the whole tree.
  - Files carrying a conflict suffix are recognised as dated, so they stay stable on later runs.
  - Camera numbers that do not fit into 4 digits (> 9999) are refused with an error and the file is left untouched.
  - A rename that `move_file` silently skips (destination already exists) is reported as a warning instead of being logged as done.
- One-time migration script `migrate_to_dated_filenames.py` (`--dry-run` supported, EXIF dates read once per file, same collision rules as above) with unit tests.

## Pending
- None for the dated filename format.

## Known limitations
- Legacy 5-6 digit names are parsed, but only numbers up to 9999 can be converted to the dated format.
- Files without EXIF dates get their date from file-system timestamps, which may not be the shoot date. QuickTime tags are stored in UTC, so videos shot around midnight can get the previous day.
- `shared/name_utils.py` and `renaming.py` are duplicated in `removealreadysortedout/`; changes must be applied to both copies (to be merged in the planned consolidation).
- Filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`) is still case-sensitive.
