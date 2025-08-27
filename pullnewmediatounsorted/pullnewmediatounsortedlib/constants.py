import os
# zdrojové složky
DEFAULT_RAID_DRIVE           = r"N:/Můj disk/Foto"
DEFAULT_DROPBOX              = r"F:/Dropbox/Camera Uploads"
DEFAULT_GDRIVE               = r"L:/Můj disk/Foto"
DEFAULT_ONEDRIVE_AUTO        = r"F:/OneDrive/Obrázky/Z fotoaparátu"
DEFAULT_ONEDRIVE_MANUAL      = r"F:/OneDrive/Obrázky/Import z fotoaparátu"
DEFAULT_SNAPBRIDGE           = r"F:/OneDrive/Obrázky/SnapBridge"
DEFAULT_SCREEN_ONEDRIVE      = r"F:/OneDrive/Obrázky/Snímky obrazovky"
DEFAULT_SCREEN_DROPBOX       = r"F:/Dropbox/Screenshots"
DEFAULT_ACCOUNT_FOLDER       = os.path.expanduser(r"~/Pictures/Camera Roll")

# cílové složky
DEFAULT_TARGET_FOLDER        = r"I:/neroztříděnoTESTING"
DEFAULT_TARGET_SCREEN_FOLDER = r"J:/Snímky obrazovky"
DEFAULT_FINAL_TARGET_FOLDER  = r"J:/"

# logování
DEFAULT_LOG_DIR              = r"H:/Logs"

# konstanty pro detekci screenshotů
SCREENSHOT_MARKERS = [
    'Sním',  # Česká část slova "Snímek obrazovky"
    'Screen'  # Anglické slovo pro screenshot
]