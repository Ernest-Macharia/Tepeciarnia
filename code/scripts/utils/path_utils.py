# utils/path_utils.py
import platform
import json
import sys
import os
from pathlib import Path

def get_app_root():
    """
    Determines the path of the running application/script's directory, 
    handling both source code and bundled executables.
    """
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).resolve()
    else:
        base_path = Path(sys.argv[0]).resolve()
    return base_path.parent

# Base paths
BASE_DIR = get_app_root()
ROOT_DIR = BASE_DIR.parent.parent
CONFIG_PATH = ROOT_DIR / "config.json"

# Collection structure
def get_collections_folder() -> Path:
    """Return the main collection folder for all wallpapers"""
    home = Path.home()
    collection_dir = home / "Pictures" / "Tapeciarnia"
    collection_dir.mkdir(parents=True, exist_ok=True)
    return collection_dir

COLLECTION_DIR = get_collections_folder()
VIDEOS_DIR = COLLECTION_DIR / "Videos"
IMAGES_DIR = COLLECTION_DIR / "Images" 
FAVS_DIR = COLLECTION_DIR / "Favorites"

# Ensure folders exist
for d in (COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR):
    d.mkdir(parents=True, exist_ok=True)

TMP_DOWNLOAD_FILE = COLLECTION_DIR / "download_path.tmp"
TRANSLATIONS_DIR = BASE_DIR / "code" / "scripts" / "translations"

# Config file init
if not CONFIG_PATH.exists():
    CONFIG_PATH.write_text(json.dumps({}), encoding="utf-8")

# Executable paths
def get_mpv_path() -> Path:
    """Get MPV executable path"""
    candidates = [
        BASE_DIR / "bin" / "mpv" / "mpv.exe",
        BASE_DIR / "bin" / "tools" / "mpv.exe",
        BASE_DIR / "bin" / "mpv.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def get_weepe_path() -> Path:
    """Get Weepe executable path for Windows wallpaper"""
    candidates = [
        BASE_DIR / "bin" / "weepe" / "weepe.exe",
        BASE_DIR / "bin" / "tools" / "weepe.exe",
        BASE_DIR / "bin" / "weepe.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def get_style_path() -> Path:
    """Get style file path"""
    return BASE_DIR / "ui" / "style" / "style.qss"

# Backward compatibility
get_app_root = get_app_root
get_weepe_path = get_weepe_path
get_mpv_path = get_mpv_path
get_style_path = get_style_path