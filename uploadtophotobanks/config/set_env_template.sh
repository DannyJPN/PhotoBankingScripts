#!/bin/bash
# Photobank Environment Variables Template
#
# INSTRUCTIONS:
# 1. Copy this file to set_photobank_env.sh (which is git-ignored)
# 2. Fill in your actual credentials
# 3. Source the file before running uploads: source set_photobank_env.sh
# 4. NEVER commit the actual credentials file!

# =============================================================================
# PHOTOBANK CREDENTIALS - REPLACE WITH YOUR ACTUAL VALUES
# =============================================================================

# ShutterStock (FTPS - Encrypted connection)
export SHUTTERSTOCK_USERNAME="your_username_or_email"
export SHUTTERSTOCK_PASSWORD="your_password"

# Pond5 (FTP - Requires separate FTP password from account settings)
export POND5_USERNAME="your_pond5_username"
export POND5_FTP_PASSWORD="your_ftp_password_from_account_settings"

# 123RF (FTP - Multiple servers for different content)
export RF123_USERNAME="your_123rf_username"
export RF123_PASSWORD="your_password"
export RF123_CONTENT_TYPE="photos"  # photos, video, or audio

# DepositPhotos (FTP)
export DEPOSITPHOTOS_EMAIL="your_email"
export DEPOSITPHOTOS_PASSWORD="your_password"

# Alamy (FTP - Multiple directories based on content type)
export ALAMY_EMAIL="your_email"
export ALAMY_PASSWORD="your_password"

# Dreamstime (FTP)
export DREAMSTIME_USERNAME="your_username_or_userid"
export DREAMSTIME_PASSWORD="your_password"

# Adobe Stock (SFTP - Encrypted, requires qualified account)
export ADOBESTOCK_SFTP_ID="your_numeric_sftp_id"
export ADOBESTOCK_SFTP_PASSWORD="your_generated_sftp_password"

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

echo "Photobank environment variables have been set."
echo ""
echo "Usage examples:"
echo "  python uploadtophotobanks.py --test-connections"
echo "  python uploadtophotobanks.py --all --dry-run"
echo "  python uploadtophotobanks.py --shutterstock --pond5"
echo ""
echo "Security reminder: This script contains passwords - keep it secure!"