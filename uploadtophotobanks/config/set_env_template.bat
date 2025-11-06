@echo off
REM Photobank Environment Variables Template (Windows)
REM
REM INSTRUCTIONS:
REM 1. Copy this file to set_photobank_env.bat (which is git-ignored)
REM 2. Fill in your actual credentials
REM 3. Run the batch file before uploads: set_photobank_env.bat
REM 4. NEVER commit the actual credentials file!

echo Setting photobank environment variables...

REM =============================================================================
REM PHOTOBANK CREDENTIALS - REPLACE WITH YOUR ACTUAL VALUES
REM =============================================================================

REM ShutterStock (FTPS - Encrypted connection)
set SHUTTERSTOCK_USERNAME=your_username_or_email
set SHUTTERSTOCK_PASSWORD=your_password

REM Pond5 (FTP - Requires separate FTP password from account settings)
set POND5_USERNAME=your_pond5_username
set POND5_FTP_PASSWORD=your_ftp_password_from_account_settings

REM 123RF (FTP - Multiple servers for different content)
set RF123_USERNAME=your_123rf_username
set RF123_PASSWORD=your_password
set RF123_CONTENT_TYPE=photos

REM DepositPhotos (FTP)
set DEPOSITPHOTOS_EMAIL=your_email
set DEPOSITPHOTOS_PASSWORD=your_password

REM Alamy (FTP - Multiple directories based on content type)
set ALAMY_EMAIL=your_email
set ALAMY_PASSWORD=your_password

REM Dreamstime (FTP)
set DREAMSTIME_USERNAME=your_username_or_userid
set DREAMSTIME_PASSWORD=your_password

REM Adobe Stock (SFTP - Encrypted, requires qualified account)
set ADOBESTOCK_SFTP_ID=your_numeric_sftp_id
set ADOBESTOCK_SFTP_PASSWORD=your_generated_sftp_password

echo.
echo Photobank environment variables have been set.
echo.
echo Usage examples:
echo   python uploadtophotobanks.py --test-connections
echo   python uploadtophotobanks.py --all --dry-run
echo   python uploadtophotobanks.py --shutterstock --pond5
echo.
echo Security reminder: This script contains passwords - keep it secure!