# MarkMediaAsChecked Implementation Status

Last updated: 2026-09-14

## Implemented
- Optional bank filter to limit status updates to selected photobanks.
- Fixed corrupted UTF-8 encoding (mojibake) and stray BOM in `markmediaaschecked.py` introduced by the original patch.
- Fixed `--banks` fail-open bug: a value that parses to no names (e.g. `,` or whitespace) now matches no status columns instead of silently falling back to all of them.
- Deduplicated repeated `--banks` entries (e.g. `AdobeStock,AdobeStock`) in the filtered column list.
- Aligned warning log call with the file's f-string convention.
- Added test coverage for the unknown-bank warning path, the fail-closed empty-banks case, deduplication, and `parse_banks()` itself.
- Moved `parse_banks()`/`filter_status_columns()` from private helpers in `markmediaaschecked.py` into `markmediaascheckedlib/mark_handler.py`, alongside the other status-column business logic, per repo project-structure convention. Tests moved to `test_mark_handler__scenarios.py` accordingly.

## Pending
- None.

## Known limitations
- Bank filtering uses prefix matching on status column names.
