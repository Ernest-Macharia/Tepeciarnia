import platform
import json
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
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