# Photobank Environment Variables Template (PowerShell)
#
# INSTRUCTIONS:
# 1. Copy this file to set_photobank_env.ps1 (which is git-ignored)
# 2. Fill in your actual credentials
# 3. Run the script before uploads: .\set_photobank_env.ps1
# 4. NEVER commit the actual credentials file!

Write-Host "Setting photobank environment variables..." -ForegroundColor Green
Write-Host ""

# =============================================================================
# PHOTOBANK CREDENTIALS - REPLACE WITH YOUR ACTUAL VALUES
# =============================================================================

# ShutterStock (FTPS - Encrypted connection)
$env:SHUTTERSTOCK_USERNAME = "your_username_or_email"
$env:SHUTTERSTOCK_PASSWORD = "your_password"

# Pond5 (FTP - Requires separate FTP password from account settings)
$env:POND5_USERNAME = "your_pond5_username"
$env:POND5_FTP_PASSWORD = "your_ftp_password_from_account_settings"

# 123RF (FTP - Multiple servers, auto-detected by file type)
$env:RF123_USERNAME = "your_123rf_username"
$env:RF123_PASSWORD = "your_password"

# DepositPhotos (FTP)
$env:DEPOSITPHOTOS_EMAIL = "your_email"
$env:DEPOSITPHOTOS_PASSWORD = "your_password"

# Alamy (FTP - Multiple directories based on content type)
$env:ALAMY_EMAIL = "your_email"
$env:ALAMY_PASSWORD = "your_password"

# Dreamstime (FTP)
$env:DREAMSTIME_USERNAME = "your_username_or_userid"
$env:DREAMSTIME_PASSWORD = "your_password"

# Adobe Stock (SFTP - Encrypted, requires qualified account)
$env:ADOBESTOCK_SFTP_ID = "your_numeric_sftp_id"
$env:ADOBESTOCK_SFTP_PASSWORD = "your_generated_sftp_password"

# =============================================================================
# VERIFICATION
# =============================================================================

Write-Host "Environment variables set for current session:" -ForegroundColor Yellow
Write-Host "  SHUTTERSTOCK_USERNAME: " -NoNewline; Write-Host $env:SHUTTERSTOCK_USERNAME -ForegroundColor Cyan
Write-Host "  POND5_USERNAME: " -NoNewline; Write-Host $env:POND5_USERNAME -ForegroundColor Cyan
Write-Host "  RF123_USERNAME: " -NoNewline; Write-Host $env:RF123_USERNAME -ForegroundColor Cyan
Write-Host "  DEPOSITPHOTOS_EMAIL: " -NoNewline; Write-Host $env:DEPOSITPHOTOS_EMAIL -ForegroundColor Cyan
Write-Host "  ALAMY_EMAIL: " -NoNewline; Write-Host $env:ALAMY_EMAIL -ForegroundColor Cyan
Write-Host "  DREAMSTIME_USERNAME: " -NoNewline; Write-Host $env:DREAMSTIME_USERNAME -ForegroundColor Cyan
Write-Host "  ADOBESTOCK_SFTP_ID: " -NoNewline; Write-Host $env:ADOBESTOCK_SFTP_ID -ForegroundColor Cyan
Write-Host ""

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

Write-Host "Environment variables have been set for this PowerShell session." -ForegroundColor Green
Write-Host ""
Write-Host "Usage examples:" -ForegroundColor White
Write-Host "  python uploadtophotobanks.py --test-connections" -ForegroundColor Gray
Write-Host "  python uploadtophotobanks.py --all --dry-run" -ForegroundColor Gray
Write-Host "  python uploadtophotobanks.py --shutterstock --pond5" -ForegroundColor Gray
Write-Host ""
Write-Host "Security reminder: This script contains passwords - keep it secure!" -ForegroundColor Red
Write-Host ""

# =============================================================================
# OPTIONAL: PERSIST FOR CURRENT USER (uncomment if needed)
# =============================================================================

# Write-Host "Do you want to set these variables permanently for your user account? [y/N]: " -NoNewline -ForegroundColor Yellow
# $persist = Read-Host
#
# if ($persist -eq "y" -or $persist -eq "Y") {
#     Write-Host "Setting permanent environment variables..." -ForegroundColor Yellow
#
#     [Environment]::SetEnvironmentVariable("SHUTTERSTOCK_USERNAME", $env:SHUTTERSTOCK_USERNAME, "User")
#     [Environment]::SetEnvironmentVariable("SHUTTERSTOCK_PASSWORD", $env:SHUTTERSTOCK_PASSWORD, "User")
#     [Environment]::SetEnvironmentVariable("POND5_USERNAME", $env:POND5_USERNAME, "User")
#     [Environment]::SetEnvironmentVariable("POND5_FTP_PASSWORD", $env:POND5_FTP_PASSWORD, "User")
#     [Environment]::SetEnvironmentVariable("RF123_USERNAME", $env:RF123_USERNAME, "User")
#     [Environment]::SetEnvironmentVariable("RF123_PASSWORD", $env:RF123_PASSWORD, "User")
#     [Environment]::SetEnvironmentVariable("DEPOSITPHOTOS_EMAIL", $env:DEPOSITPHOTOS_EMAIL, "User")
#     [Environment]::SetEnvironmentVariable("DEPOSITPHOTOS_PASSWORD", $env:DEPOSITPHOTOS_PASSWORD, "User")
#     [Environment]::SetEnvironmentVariable("ALAMY_EMAIL", $env:ALAMY_EMAIL, "User")
#     [Environment]::SetEnvironmentVariable("ALAMY_PASSWORD", $env:ALAMY_PASSWORD, "User")
#     [Environment]::SetEnvironmentVariable("DREAMSTIME_USERNAME", $env:DREAMSTIME_USERNAME, "User")
#     [Environment]::SetEnvironmentVariable("DREAMSTIME_PASSWORD", $env:DREAMSTIME_PASSWORD, "User")
#     [Environment]::SetEnvironmentVariable("ADOBESTOCK_SFTP_ID", $env:ADOBESTOCK_SFTP_ID, "User")
#     [Environment]::SetEnvironmentVariable("ADOBESTOCK_SFTP_PASSWORD", $env:ADOBESTOCK_SFTP_PASSWORD, "User")
#
#     Write-Host "Permanent environment variables set. Restart your terminal to use them in new sessions." -ForegroundColor Green
# } else {
#     Write-Host "Variables set only for current session." -ForegroundColor Gray
# }