# ExportPreparedMedia - Version History

## Version 1.0 - Functional Release
**Date:** 2025-01-24  
**Status:** First version providing correct results

### Features
- Default --all parameter with mutual exclusion logic
- Fixed zero division error handling for empty bank results
- Proper output path generation with separate directory and prefix
- Support for all major photobanks with bank-specific formatting
- Comprehensive category mapping and metadata generation

### Technical Details
- Separated DEFAULT_OUTPUT_FOLDER into DEFAULT_OUTPUT_DIR and DEFAULT_OUTPUT_PREFIX
- Fixed path generation using os.path.join for proper directory structure
- Added attempted_count > 0 check to prevent division by zero
- Maintains backward compatibility with individual bank parameters