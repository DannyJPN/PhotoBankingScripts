# RemoveAlreadySortedOut Implementation Status

Last updated: 2026-09-19

## Implemented
- Removal of files from the unsorted folder that already exist in the target folder.
- Duplicate detection by content hash (`get_target_hash_map`, `find_duplicates`, `handle_duplicate`), independent of file names, so renamed files are still recognised.
- A source file is deleted only when at least one matching target file really exists on disk.
- Dated filename helpers (`shared/name_utils.py`, `normalize_indexed_filenames`) mirroring `pullnewmediatounsorted/`:
  - format `<prefix><YYYYMMDD>_<XXXX>.<ext>`, idempotent, `_B`/`_C` suffixes on same-day conflicts;
  - camera numbers above 9999 are refused and the file is left untouched;
  - a rename skipped by `move_file` because the destination exists is logged as a warning.

## Pending
- None for the dated filename format.

## Known limitations
- `normalize_indexed_filenames` is not called from `remove_already_sorted_out.py` (hash-based detection makes the pre-rename unnecessary).
- Files renamed with a `_B`/`_C` conflict suffix are not recognised as dated on later runs.
- `extract_dated_parts` does not validate that the 8-digit date is a real calendar date.
- `shared/name_utils.py` and `renaming.py` are duplicated in `pullnewmediatounsorted/`; changes must be applied to both copies.
