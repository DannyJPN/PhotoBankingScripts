# RemoveAlreadySortedOut Implementation Status

Last updated: 2026-09-20

## Implemented
- Removal of files from the unsorted folder that already exist in the target folder.
- Duplicate detection by content hash (`get_target_hash_map`, `find_duplicates`, `handle_duplicate`), independent of file names, so renamed files are still recognised.
- A source file is deleted only when at least one matching target file really exists on disk.
- Dated filename helpers (`shared/name_utils.py`, `normalize_indexed_filenames`) mirroring `pullnewmediatounsorted/`:
  - format `<prefix><YYYYMMDD>_<XXXX>.<ext>`, idempotent; the date is an output only and is never read back;
  - case-insensitive name comparison (Windows/NTFS semantics);
  - identical content under the same name is a duplicate, not a conflict; different content gets `_B`, `_C`, ...;
  - files carrying a conflict suffix are recognised as dated;
  - camera numbers above 9999 are refused and the file is left untouched;
  - a rename skipped by `move_file` because the destination exists is logged as a warning.

## Pending
- None for the dated filename format.

## Known limitations
- `normalize_indexed_filenames` is not called from `remove_already_sorted_out.py` (hash-based detection makes the pre-rename unnecessary).
- `shared/name_utils.py` and `renaming.py` are duplicated in `pullnewmediatounsorted/`; changes must be applied to both copies (to be merged in the planned consolidation).
- Filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`) is still case-sensitive.
