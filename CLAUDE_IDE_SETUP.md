# Claude Code IDE Setup Guide

This document provides setup instructions for using Claude Code with local IDEs, specifically addressing Windows/PyCharm configuration issues.

## Configuration Files Overview

The repository now includes **two different configuration formats** for Claude Code:

### 1. GitHub Actions Configuration
- **File**: `.github/workflows/claude.yml`
- **Format**: YAML
- **Usage**: Automatic triggers on GitHub issue comments, PR reviews
- **Authentication**: Uses GitHub repository secrets (`CLAUDE_CODE_OAUTH_TOKEN`)

### 2. Local IDE Configuration  
- **Files**: `settings.json` (primary) and `.claude/settings.json` (backup)
- **Format**: JSON
- **Usage**: Direct IDE integration (PyCharm, VSCode, etc.)
- **Authentication**: Requires personal Claude Code OAuth token

## Local IDE Setup Instructions

### For Windows/PyCharm Users:

1. **Pull Latest Changes**
   ```bash
   git pull origin master
   ```

2. **Verify Configuration Files**
   Ensure these files exist in your project:
   - `settings.json` (project root)
   - `.claude/settings.json` (backup location)
   - `CLAUDE.md` (project instructions)

3. **Authentication Setup**
   
   Choose **one** of these methods:

   **Option A: Environment Variable (Recommended)**
   ```bash
   # In Git Bash or your terminal
   export CLAUDE_CODE_OAUTH_TOKEN="your_oauth_token_here"
   ```
   
   **Option B: Private Settings File**
   Create `.claude/settings_private.json`:
   ```json
   {
     "oauth_token": "your_oauth_token_here"
   }
   ```
   *(This file is gitignored for security)*

4. **Test Configuration**
   ```bash
   # Navigate to project root in Git Bash
   cd /path/to/PhotoBankingScripts
   
   # Test the configuration
   /permissions
   ```
   
   **Expected Output**: You should see a list of allowed tools instead of empty lists.

5. **Restart PyCharm**
   - Close PyCharm completely
   - Reopen the project
   - Open Git Bash terminal within PyCharm
   - Test the `/permissions` command again

## Configuration Details

### settings.json Format (Local IDE)
```json
{
  "model": "claude-sonnet-4",
  "custom_instructions": "./CLAUDE.md",
  "allowed_tools": [
    {
      "name": "Bash",
      "commands": [
        "pytest",
        "python -m pytest",
        "black .",
        "ruff check",
        "git status"
      ]
    },
    {
      "name": "Read",
      "enabled": true
    }
  ],
  "environment": {
    "PYTHONPATH": ".",
    "PYTHON_ENV": "development"
  }
}
```

### GitHub Actions Format (YAML)
```yaml
uses: anthropics/claude-code-action@beta
with:
  claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
  allowed_tools: "Bash(pytest),Bash(black .),Bash(ruff check)"
  custom_instructions: |
    Follow Python PEP 8 standards
    Use type hints everywhere
```

## Troubleshooting

### Issue: `/permissions` Shows Empty Lists
- **Cause**: Missing `settings.json` files or authentication
- **Solution**: Follow setup instructions above, ensure authentication is configured

### Issue: "Configuration Not Found"
- **Cause**: Claude Code looking in wrong directory
- **Solution**: Verify you're in the project root directory, check file paths

### Issue: Authentication Errors
- **Cause**: Invalid or missing OAuth token
- **Solution**: 
  1. Verify your Claude Code OAuth token is valid
  2. Check environment variable spelling: `CLAUDE_CODE_OAUTH_TOKEN`
  3. Restart terminal/PyCharm after setting environment variables

### Issue: Tools Not Working in IDE
- **Cause**: Different configuration formats between GitHub Actions and IDE
- **Solution**: This has been fixed - both configurations are now properly set up

## File Structure
```
PhotoBankingScripts/
├── settings.json                 # Primary IDE configuration
├── .claude/
│   └── settings.json            # Backup IDE configuration
├── .github/workflows/
│   └── claude.yml               # GitHub Actions configuration
├── CLAUDE.md                    # Project-specific instructions
└── CLAUDE_IDE_SETUP.md         # This setup guide
```

## Verification Steps

After setup, verify everything works:

1. **In Git Bash (project root):**
   ```bash
   /permissions
   ```
   Should show configured tools.

2. **Test a simple command:**
   ```bash
   /git status
   ```
   Should show git repository status.

3. **Test Claude Code functionality:**
   ```bash
   /read CLAUDE.md
   ```
   Should display the project instructions.

If all tests pass, your Claude Code IDE integration is properly configured!

## Support

If you continue experiencing issues:
1. Check that you're using the latest version of Claude Code
2. Verify all file permissions are correct
3. Try restarting your IDE and terminal
4. Check the Claude Code documentation for your specific IDE integration