# Claude Code Configuration Setup

This document explains how to properly configure Claude Code for local development, especially in JetBrains PyCharm on Windows.

## Configuration Files Created

### 1. `settings.json` (Project Root)
**Location**: `/PhotoBankingScripts/settings.json`  
**Purpose**: Main configuration file for Claude Code  
**Contains**:
- Model specification
- Custom instructions referencing CLAUDE.md
- Allowed tools for Python development
- Environment variables

### 2. `.claude/settings.json` (Backup Location)
**Location**: `/PhotoBankingScripts/.claude/settings.json`  
**Purpose**: Alternative configuration location  
**Note**: Claude Code checks both locations, project root takes precedence

### 3. `CLAUDE.md` (Already Exists)
**Location**: `/PhotoBankingScripts/CLAUDE.md`  
**Purpose**: Project-specific instructions and coding standards  
**Status**: ✅ Already properly configured

## For Windows/PyCharm Users

### Verification Steps

1. **Check Working Directory in PyCharm Git Bash**:
   ```bash
   pwd
   # Should show: /path/to/PhotoBankingScripts
   ```

2. **Verify Configuration Files**:
   ```bash
   ls -la settings.json
   ls -la .claude/settings.json
   ls -la CLAUDE.md
   ```

3. **Test Claude Code Recognition**:
   ```bash
   # In Claude Code terminal
   /permissions
   # Should now show allowed tools instead of empty lists
   ```

### Authentication Setup

The `settings.json` files created do **NOT** contain authentication tokens for security reasons. To add authentication:

#### Option 1: Environment Variable (Recommended)
```bash
export CLAUDE_CODE_OAUTH_TOKEN="your_token_here"
```

#### Option 2: Private Settings File
Create `.claude/settings_private.json` (gitignored):
```json
{
  "claude_code_oauth_token": "your_token_here"
}
```

### Troubleshooting Common Issues

#### Issue: Empty `/permissions` command
- **Cause**: Configuration files not found
- **Solution**: Verify working directory and file presence

#### Issue: Windows Path Resolution
- **Cause**: Git Bash vs Windows native paths
- **Solution**: Use forward slashes in paths within settings.json

#### Issue: File Encoding
- **Cause**: Windows line endings or BOM
- **Solution**: Ensure UTF-8 without BOM encoding

#### Issue: PyCharm Working Directory
- **Cause**: PyCharm may start in subdirectory
- **Solution**: Set PyCharm terminal to start in project root

## File Structure Verification

Your project should now have:
```
PhotoBankingScripts/
├── settings.json              ← Main config (NEW)
├── .claude/
│   └── settings.json          ← Backup config (NEW)  
├── CLAUDE.md                  ← Project instructions (EXISTS)
├── .gitignore                 ← Updated to ignore sensitive configs
└── README_CLAUDE_SETUP.md     ← This file (NEW)
```

## Security Notes

- Generic configuration files are tracked in Git
- Authentication tokens should NEVER be committed
- Use environment variables or gitignored private files for secrets
- The `.gitignore` has been updated to prevent accidental token commits

## Testing the Setup

1. Restart PyCharm
2. Open Git Bash terminal in PyCharm
3. Navigate to project root
4. Run: `/permissions`
5. Should see configured allowed tools instead of empty lists

If issues persist, check:
- Working directory is project root
- Files have correct UTF-8 encoding
- No syntax errors in JSON files