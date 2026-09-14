# MarkMediaAsChecked Implementation Status

Last updated: 2026-09-14

## Implemented
- Optional bank filter to limit status updates to selected photobanks.
- Fixed corrupted UTF-8 encoding (mojibake) and stray BOM in `markmediaaschecked.py` introduced by the original patch.
- Added test coverage for the unknown-bank warning path.

## Pending
- None.

## Known limitations
- Bank filtering uses prefix matching on status column names.
