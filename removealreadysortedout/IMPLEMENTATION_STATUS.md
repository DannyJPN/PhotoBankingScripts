# RemoveAlreadySortedOut Implementation Status

Last updated: 2026-11-09

## Implemented
- Removal of files from the unsorted folder that already exist in the target folder.
- Duplicate detection by content hash (`get_target_hash_map`, `find_duplicates`, `handle_duplicate`), independent of file names, so files renamed to the dated format are still recognised.
- A source file is deleted only when at least one matching target file really exists on disk. A failed deletion is logged and does not abort the removal of the remaining duplicates.
- Right before deletion both the source and the matching target are hashed again; if either changed since the scan or cannot be read, the source is kept. The number of kept candidates is reported at the end of the run.
- Empty (0-byte) files are never treated as duplicates: they all share one hash. They are skipped with a warning; skipped and unreadable files are summarised at the end of the scan.
- The target folder is hashed only once per run: `unify_duplicate_files` returns its final path → hash map and `get_target_hash_map` reuses it. Filename pattern replacement therefore runs before unification.
- Generic filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`) retains both files and warns on a name collision; names alone never authorize deletion. No-overwrite moves use exclusive hard links to avoid overwriting a concurrently created target.
- The dated filename normalization (`normalize_indexed_filenames` and the `name_utils` helpers) was removed from this script: hash-based detection made the pre-rename step unnecessary and nothing called it. The living implementation is in `pullnewmediatounsorted/`.

## Pending
- None.

## Known limitations
- Breaking CLI change: `--overwrite`, `--index_prefix`, `--index_width` and `--index_max` were removed. Legacy normalization now belongs to `pullnewmediatounsorted`; this script detects duplicates by hash instead. Wrappers must stop passing the removed options. No uses were found in tracked Python, PowerShell, batch or shell launch scripts during the review.
- No-overwrite moves require hard-link support on the same filesystem; unsupported moves fail without a copy/delete fallback.
- Filename pattern replacement (`replace_in_filenames`, `_NIK` -> `NIK_`) is case-sensitive.
