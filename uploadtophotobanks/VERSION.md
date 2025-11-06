# Upload to Photobanks - Version History

## Version 1.0.0 (2025-09-20)

### Initial Release

**Features:**
- Automated upload to 7 major photobank services
- Support for FTP, FTPS, and SFTP protocols
- Secure credentials management
- File validation against photobank requirements
- Dry-run mode for testing
- Progress tracking with detailed statistics
- Comprehensive logging

**Supported Photobanks:**
- Shutterstock (FTPS) - Encrypted connection
- Pond5 (FTP) - Separate release folder support
- 123RF (FTP) - Multiple servers for different content types
- DepositPhotos (FTP) - Vector ZIP handling
- Alamy (FTP) - Multi-directory structure (Stock/News/Archive/Vectors)
- Dreamstime (FTP) - Content-type based directory routing
- Adobe Stock (SFTP) - Qualified accounts only, encrypted connection

**Security Features:**
- Encrypted connections where supported (Shutterstock FTPS, Adobe Stock SFTP)
- Separate credentials storage
- Connection validation
- Passive mode for firewall compatibility

**File Support:**
- Images: JPEG, TIFF, PNG (photobank-dependent)
- Vectors: EPS, AI, SVG (with validation)
- Video: MP4, MOV, AVI (size and duration validation)
- Audio: WAV, MP3, FLAC (Pond5, 123RF)

**Validation Features:**
- Minimum megapixel requirements per photobank
- File size limits validation
- Format compatibility checking
- Companion file detection (JPEG with vectors)

**Command Line Interface:**
- Individual photobank selection
- Bulk upload to all configured services
- Interactive credentials setup
- Connection testing
- File listing without upload
- Template generation

**Based on Documentation:**
- Comprehensive research of FTP/SFTP protocols for each photobank
- Security best practices implementation
- Photobank-specific requirements and limitations
- Error handling and retry logic

**Architecture:**
- Modular design following existing codebase patterns
- Shared logging and utilities
- Type hints and documentation
- Progress bars and user feedback
- Centralized configuration management