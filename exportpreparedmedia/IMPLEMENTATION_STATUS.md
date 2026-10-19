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
  - Batches are counted per group; the `_<batch>` suffix appears only when a group needs more than one file.
  - Existing bank files that the run did not write (legacy `CSV_<Bank>.csv`, old batch or group files) are kept
    and reported with a warning as out of date.
  - `EDITORIAL_REGEX` also matches multi-word city names.
  - Functions: `get_edit_type`, `get_group_output_file`, `group_records_by_edit_type`, `find_stale_outputs`,
    `_write_batch` in `exportpreparedmedialib/exporters.py`.
  - Tests: `tests/unit/test_exporters__edit_type_split__scenarios.py`.

## Pending

- Stale output files are only reported, not removed.

## Known limitations

- Pre-existing test failures on master (unchanged by the split): `test_exportpreparedmedia__main__scenarios.py`
  (test args miss newer bank switches), `test_main_pipeline__filters_and_exports.py`,
  `test_main__rejects_all_with_individual.py`, `test_banks_logic__scenarios.py::test_extract_media_properties__basic_fields`,
  import smoke tests of `category_handler`, `export_processor`, `csv_handler`, logging config and media filter tests.
