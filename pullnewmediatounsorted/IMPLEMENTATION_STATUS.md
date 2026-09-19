# PullNewMediaToUnsorted Implementation Status

Last updated: 2026-09-19

## Implemented
- Pulling new media from the configured sources into the unsorted folder, flattening and deduplicating by content hash.
- Dated filename format `<prefix><YYYYMMDD>_<XXXX>.<ext>` (e.g. `NIK_20260612_8888.JPG`), replacing the sequential counter with its 999 999 ceiling.
  - The date is the oldest available EXIF/file date (`get_best_creation_date`); the 4-digit camera sequence number is kept from the original name.
  - `normalize_indexed_filenames` is idempotent: an already-dated file is never renamed again, and a hash match against the reference folder reuses the reference's canonical name.
  - Same-day counter collisions are resolved with `_B`, `_C`, ... suffixes.
  - Camera numbers that do not fit into 4 digits (> 9999) are refused with an error and the file is left untouched, because a wider number would not round-trip through `extract_dated_parts`.
  - A rename that `move_file` silently skips (destination already exists) is reported as a warning instead of being logged as done.
- One-time migration script `migrate_to_dated_filenames.py` (`--dry-run` supported, EXIF dates read once per file).

## Pending
- None for the dated filename format.

## Known limitations
- Files renamed with a `_B`/`_C` conflict suffix are not recognised as dated on later runs and are skipped.
- `extract_dated_parts` does not validate that the 8-digit date is a real calendar date.
- Legacy 5-6 digit names are parsed, but only numbers up to 9999 can be converted to the dated format.
- Files without EXIF dates get their date from file-system timestamps, which may not be the shoot date.
- `shared/name_utils.py` is duplicated in `removealreadysortedout/`; changes must be applied to both copies.
