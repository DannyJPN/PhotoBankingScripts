# PullNewMediaToUnsorted Implementation Status

Last updated: 2026-10-08

## Implemented
- Pulling new media from the configured sources into the unsorted folder, flattening and deduplicating by content hash.
- Dated filename format `<prefix><YYYYMMDD>_<XXXX>.<ext>` (e.g. `NIK_20260612_8888.JPG`), replacing the sequential counter with its 999 999 ceiling.
  - The date is the oldest available EXIF/file date (`get_best_creation_date`). It is an output for the user and the file system that keeps the name unique without a variable length; the scripts never read it back. The 4-digit camera sequence number is kept from the original name.
  - Only legacy names (`<prefix>` + 4-6 digits, anchored at the start of the name) enter `normalize_indexed_filenames`. A file that already has a dated name keeps it forever, whatever its EXIF or file dates are. A hash match against the reference folder reuses the reference's canonical name.
  - All source folders are normalized in one call with one shared name space, so two different files from two different sources can never get the same name. Before, each source was compared only with the target, and two different shots could get the same name in two sources.
  - All name comparisons are case-insensitive (Windows/NTFS semantics, `name_key`), including the prefix match when files are listed, so `nik_0042.JPG` is normalized too.
  - A name collision with a file of identical content (same hash) is a duplicate copy, not a conflict: the name is kept and no suffix is added. A collision with different content gets `_B`, `_C`, ... and names stay unique across the whole tree.
  - Files carrying a conflict suffix are recognised as dated, so they stay stable on later runs.
  - Camera numbers that do not fit into 4 digits (> 9999) are refused with an error and the file is left untouched.
  - A rename that `move_file` silently skips (destination already exists) is reported as a warning instead of being logged as done.
  - When a rename fails or is skipped, a file gets its old name back in the name bookkeeping only if it owned that name, so a second file with the same legacy name in another source keeps its ownership.
  - Files left unrenamed are summarised at the end of each prefix run with counts per reason (hash error, no camera number, camera number out of range, no free name variant, destination exists, rename failed).
- `copy_file` never replaces an existing file with different content. An identical existing file is skipped; a different one is logged as a content conflict, left untouched and the source file is not copied (`FileExistsError`). `copy_folder` keeps copying the remaining files and reports the conflict count. The check guards against files corrupted during the run; resolving name collisions is not its job.
- One-time migration script `migrate_to_dated_filenames.py` (`--dry-run` supported, EXIF dates read once per file, same collision rules as above) with unit tests.

## Pending
- None for the dated filename format.

## Known limitations
- Legacy 5-6 digit names are parsed, but only numbers up to 9999 can be converted to the dated format.
- Files without EXIF dates get their date from file-system timestamps, which may not be the shoot date. QuickTime tags are stored in UTC, so videos shot around midnight can get the previous day.
- Unique camera prefixes are required: two cameras sharing one prefix can produce the same date and sequence number for different shots.
- Only files with a prefix from `PREFIXES_TO_NORMALIZE` get unique names. Other files (phones, screenshots) with the same relative path in two sources are not renamed; `copy_file` reports them as content conflicts and does not copy the second one.
- The one-time migration script processes one folder per run, so J:/ and I:/ were not checked against each other.
- Filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`) is still case-sensitive.
