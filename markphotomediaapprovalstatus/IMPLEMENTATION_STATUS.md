# markphotomediaapprovalstatus - Implementation Status

## Public Portfolio Approval Detection Feature

### Overview
Automatic detection of approved photos on photobanks via public web scraping.
When a photo appears in the contributor's public portfolio, it means the bank has approved it.

### Working Banks (4)

| Bank | Status | Assets Extracted |
|------|--------|------------------|
| AdobeStock | OK | 88 |
| DepositPhotos | OK | 31 |
| 123RF | OK | 69 |
| GettyImages (iStock) | OK | 100 |

### Blocked Banks - Need Cookie Session (4)

These banks use DataDome anti-bot protection. Manual CAPTCHA solving is required.

| Bank | Solution |
|------|----------|
| ShutterStock | Run `python save_bank_session.py --bank ShutterStock` |
| Dreamstime | Run `python save_bank_session.py --bank Dreamstime` |
| Pond5 | Run `python save_bank_session.py --bank Pond5` |
| BigStockPhoto | Run `python save_bank_session.py --bank BigStockPhoto` |

**How to unblock:**
1. Run `python save_bank_session.py --bank <BankName>`
2. Browser opens with the portfolio page
3. Solve the CAPTCHA manually
4. Wait for page to load completely
5. Cookies are saved automatically
6. The bank will work in subsequent automated runs

### Banks Without Portfolio URL (1)

| Bank | Reason |
|------|--------|
| Alamy | Portfolio URL not configured |

### Unsupported Banks (8)

These banks don't have public portfolio pages or are deprecated:

- CanStockPhoto (deprecated)
- Pixta
- Freepik
- Vecteezy
- StoryBlocks
- Envato
- 500px
- MostPhotos

### Key Files

- `markphotomediaapprovalstatuslib/public_portfolio/` - Main module
  - `runner.py` - Main processing logic
  - `browser.py` - Playwright browser with cookie support
  - `matching.py` - Title matching logic
  - `banks/` - Bank-specific adapters
- `save_bank_session.py` - Helper for manual CAPTCHA solving
- `cookies/` - Saved session cookies per bank

### Configuration

Portfolio URLs are defined in:
- `markphotomediaapprovalstatuslib/public_portfolio/constants.py`

### Usage

```python
from markphotomediaapprovalstatuslib.public_portfolio.runner import process_public_portfolio_approval

# Process all records and update status
changes_made = process_public_portfolio_approval(
    all_data=records,
    filtered_data=checked_records,
    csv_path="PhotoMedia.csv",
    headless=True,
)
```

### Timeouts Configuration

- Page load timeout: 120 seconds
- Initial wait after load: 10 seconds
- Scroll wait: 5 seconds per scroll
- Max scrolls: 30 (for infinite scroll pages)

---
Last updated: 2026-01-27