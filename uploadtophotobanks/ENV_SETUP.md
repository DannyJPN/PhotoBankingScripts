# Environment Variables Setup

The uploadtophotobanks script prioritizes **environment variables** for credentials security. This prevents accidentally committing passwords to git repositories.

## How It Works

1. **Environment variables are checked first** - if found, no config file is needed
2. **Config file is fallback** - only loaded for photobanks missing from environment
3. **No real credentials in git** - .gitignore prevents committing actual passwords

## Environment Variables

### ShutterStock (FTPS - Encrypted)
```bash
export SHUTTERSTOCK_USERNAME="your_username_or_email"
export SHUTTERSTOCK_PASSWORD="your_password"
```

### Pond5 (FTP - requires separate FTP password)
```bash
export POND5_USERNAME="your_pond5_username"
export POND5_FTP_PASSWORD="your_ftp_password_from_account_settings"
# Alternative names also work:
# export POND5_PASSWORD="your_ftp_password"
```

### 123RF (FTP - multiple servers)
```bash
export RF123_USERNAME="your_123rf_username"
export RF123_PASSWORD="your_password"
export RF123_CONTENT_TYPE="photos"  # Optional: photos/video/audio
```

### DepositPhotos (FTP)
```bash
export DEPOSITPHOTOS_EMAIL="your_email"  # or DEPOSITPHOTOS_USERNAME
export DEPOSITPHOTOS_PASSWORD="your_password"
```

### Alamy (FTP)
```bash
export ALAMY_EMAIL="your_email"  # or ALAMY_USERNAME
export ALAMY_PASSWORD="your_password"
```

### Dreamstime (FTP)
```bash
export DREAMSTIME_USERNAME="your_username_or_userid"
export DREAMSTIME_PASSWORD="your_password"
```

### Adobe Stock (SFTP - Encrypted, qualification required)
```bash
export ADOBESTOCK_SFTP_ID="your_numeric_sftp_id"
export ADOBESTOCK_SFTP_PASSWORD="your_generated_sftp_password"
```

### Freepik (SFTP - Encrypted, requires Level 3 contributor with 500+ published files)
```bash
export FREEPIK_FTP_ID="your_ftp_id_from_dashboard"
export FREEPIK_FTP_PASSWORD="your_ftp_password"
```

### MostPhotos (FTP - credentials from contributor dashboard)
```bash
export MOSTPHOTOS_USERNAME="your_ftp_username"
export MOSTPHOTOS_PASSWORD="your_ftp_password"
```

### Web-Only Photobanks (No FTP/SFTP Upload)
The following photobanks use web-based upload only and do not require credentials here:
- **Pixta**: CSV metadata upload via web interface
- **Vecteezy**: Manual web upload
- **StoryBlocks**: Contributor portal upload
- **Envato**: Portfolio Manager upload (IPTC metadata only)
- **500px**: Manual web upload (API deprecated 2018)

## Setup Methods

### Option 1: Shell Script (Recommended)
Create `set_photobank_env.sh` (never commit this file!):

```bash
#!/bin/bash
# Photobank credentials - DO NOT COMMIT THIS FILE!

# ShutterStock
export SHUTTERSTOCK_USERNAME="your_actual_username"
export SHUTTERSTOCK_PASSWORD="your_actual_password"

# Pond5
export POND5_USERNAME="your_actual_username"
export POND5_FTP_PASSWORD="your_actual_ftp_password"

# Add other photobanks as needed...

echo "Photobank environment variables set"
```

Usage:
```bash
source set_photobank_env.sh
python uploadtophotobanks.py --all --dry-run
```

### Option 2: System Environment
Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Photobank credentials
export SHUTTERSTOCK_USERNAME="your_username"
export SHUTTERSTOCK_PASSWORD="your_password"
# ... etc
```

### Option 3: .env File (with python-dotenv)
Create `.env` file (never commit!):

```bash
# Photobank credentials
SHUTTERSTOCK_USERNAME=your_username
SHUTTERSTOCK_PASSWORD=your_password
POND5_USERNAME=your_username
POND5_FTP_PASSWORD=your_ftp_password
```

## Fallback Config File

If some photobanks are not in environment variables, create `config/credentials.json`:

```json
{
  "SomePhotobank": {
    "username": "fallback_username",
    "password": "fallback_password"
  }
}
```

**Important:** This file is git-ignored and won't be committed.

## Security Best Practices

1. **Never commit real credentials** - use environment variables or git-ignored files
2. **Use encrypted connections** where available (Shutterstock FTPS, Adobe Stock SFTP)
3. **Separate FTP passwords** for Pond5 - generate in account settings
4. **Qualified accounts only** for Adobe Stock SFTP
5. **Regular password rotation** - change credentials periodically

## Testing Setup

Verify your credentials without uploading:

```bash
# Test all connections
python uploadtophotobanks.py --test-connections

# List what would be uploaded
python uploadtophotobanks.py --all --dry-run

# Test specific photobank
python uploadtophotobanks.py --shutterstock --dry-run
```

## Troubleshooting

### "No credentials configured"
- Check environment variables are set: `echo $SHUTTERSTOCK_USERNAME`
- Verify variable names match exactly (case-sensitive)
- Ensure fallback config file exists if needed

### "Connection failed"
- Verify username/password are correct
- For Pond5: ensure you're using FTP password, not account password
- For Adobe Stock: ensure account is qualified for SFTP
- Check network connectivity

### "Authentication failed"
- Double-check credentials in photobank account
- For Adobe Stock: use numeric SFTP ID, not email
- For Pond5: generate new FTP password if needed

## Alternative Variable Names

The system checks multiple environment variable names for flexibility:

- `SHUTTERSTOCK_USERNAME` or `SHUTTERSTOCK_USER`
- `POND5_PASSWORD` or `POND5_PASS` or `POND5_FTP_PASSWORD`
- `DEPOSITPHOTOS_USERNAME` or `DEPOSITPHOTOS_USER` or `DEPOSITPHOTOS_EMAIL`

Use whichever naming convention you prefer.