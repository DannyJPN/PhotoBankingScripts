# UploadToPhotobanks - Implementation Status

**Last Updated:** 2026-10-19

## Implemented

- Upload of media files to photobanks over FTP/FTPS/SFTP (`PhotobankUploader`, `ConnectionManager`).
- File validation per photobank (`FileValidator`), dry-run mode.
- Export CSV check before upload: `<Bank>Output.csv` if present, otherwise all of `CSV_<Bank>.csv` and the split
  exports `CSV_<Bank>_*.csv` written by exportpreparedmedia (per edit type, editorial and batch) (2026-10-19,
  `PhotobankUploader._find_export_csvs`, tests in `tests/unit/test_uploader__find_export_csvs__scenarios.py`).

## Pending

- The filenames loaded from export CSVs are not yet used to restrict which media files get uploaded.

## Known limitations

- Pre-existing test failures on master: `test_credentials_manager__scenarios.py::test_load_missing_from_file`,
  logging config tests.
