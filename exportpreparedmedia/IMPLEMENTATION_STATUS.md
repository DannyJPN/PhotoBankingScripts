# ExportPreparedMedia - Implementation Status

**Last Updated:** 2026-10-19

## Implemented

- Export of PhotoMedia.csv records with status `kontrolováno` to bank-specific CSVs (`--<bank>` switches or `--all`).
- Optional inclusion of edited photos (`--include-edited`) and alternative formats (`--include-alternative-formats`).
- Editorial records are excluded for banks in `BANKS_NO_EDITORIAL` (AdobeStock, GettyImages, Freepik, Pixta).
- Batch splitting for banks with batch size limits (`PHOTOBANK_BATCH_SIZE_LIMITS`, GettyImages: 100).
- **Split per edit type and editorial flag (2026-10-19):** every bank export is written as
  `<prefix>_<Bank>[_editorial]_<edit type>[_<batch>].csv`, e.g. `CSV_Pond5_bw.csv`,
  `CSV_Pond5_editorial_original.csv`, `CSV_GettyImages_negative_2.csv`.
  - Edit type is the last edit tag of the filename (`original`, `sharpen`, `bw`, `negative`, `misty`, `blurred`),
    the same rule as the createbatch edit subfolders (`X_sharpen_bw.jpg` is `bw`).
  - Batches match createbatch: records (before adding PNG/TIF versions) are cut into batches, commercial and
    editorial counted separately, then each batch is split per edit type. Banks with a batch size limit always
    carry the batch number (`CSV_GettyImages_bw_2.csv` = `GettyImages/batch_002/jpg/_bw/`).
  - Edit-type files of the bank that this run did not write are kept and reported as out of date. The deprecated
    `CSV_<Bank>.csv` and old `CSV_<Bank>_<N>.csv` batches are ignored.
  - A bank without a header is an error: no file is written, nothing is appended to an older file.
  - The run ends with a summary; any file not written or record not exported logs an error and exits with code 1.
  - `EDITORIAL_REGEX` also matches multi-word and hyphenated city names (ASCII letters only).
  - Functions: `get_edit_type`, `get_group_output_file`, `group_records_by_edit_type`, `split_into_batches`,
    `find_stale_outputs`, `_write_batch` in `exportpreparedmedialib/exporters.py`.
  - Tests: `tests/unit/test_exporters__edit_type_split__scenarios.py`,
    `tests/unit/test_exportpreparedmedia__main__export_summary.py`; parity with createbatch in
    `tests/unit/test_editorial_split__createbatch_export_parity.py` (repository root).

## Pending

- Out-of-date edit-type files are only reported, not removed.

## Known limitations

- Pre-existing test failures on master (unchanged by the split): `test_exportpreparedmedia__main__scenarios.py`
  (test args miss newer bank switches), `test_main_pipeline__filters_and_exports.py`,
  `test_main__rejects_all_with_individual.py`, `test_banks_logic__scenarios.py::test_extract_media_properties__basic_fields`,
  import smoke tests of `category_handler`, `export_processor`, `csv_handler`, logging config and media filter tests.
