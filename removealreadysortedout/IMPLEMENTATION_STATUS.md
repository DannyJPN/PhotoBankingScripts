# RemoveAlreadySortedOut Implementation Status

Last updated: 2026-10-08

## Implemented
- Removal of files from the unsorted folder that already exist in the target folder.
- Duplicate detection by content hash (`get_target_hash_map`, `find_duplicates`, `handle_duplicate`), independent of file names, so files renamed to the dated format are still recognised.
- A source file is deleted only when at least one matching target file really exists on disk. A failed deletion is logged and does not abort the removal of the remaining duplicates.
- Right before deletion both the source and the matching target are hashed again; if either changed since the scan or cannot be read, the source is kept. The number of kept candidates is reported at the end of the run.
- Empty (0-byte) files are never treated as duplicates: they all share one hash. They are skipped with a warning; skipped and unreadable files are summarised at the end of the scan.
- The target folder is hashed only once per run: `unify_duplicate_files` returns its final path → hash map and `get_target_hash_map` reuses it. Filename pattern replacement therefore runs before unification.
- Generic filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`).
- The dated filename normalization (`normalize_indexed_filenames` and the `name_utils` helpers) was removed from this script: hash-based detection made the pre-rename step unnecessary and nothing called it. The living implementation is in `pullnewmediatounsorted/`.

## Pending
- None.

## Known limitations
- Filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`) is case-sensitive.
