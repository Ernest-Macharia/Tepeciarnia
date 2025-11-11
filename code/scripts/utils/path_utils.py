# utils/path_utils.py
import platform
import json
import sys
import os
import logging
from pathlib import Path

# Get logger for this module
logger = logging.getLogger(__name__)


def get_app_root():
    """
    Determines the path of the running application/script's directory, 
    handling both source code and bundled executables.
    """
    logger.debug("Determining application root path")
    
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).resolve()
        logger.debug(f"Running as frozen executable, using: {base_path}")
    else:
        base_path = Path(sys.argv[0]).resolve()
        logger.debug(f"Running as Python script, using: {base_path}")
    
    app_root = base_path.parent
    logger.info(f"Application root determined: {app_root}")
    return app_root


# Base paths
logger.debug("Initializing base paths")
BASE_DIR = get_app_root()
ROOT_DIR = BASE_DIR.parent.parent
CONFIG_PATH = ROOT_DIR / "config.json"

logger.debug(f"BASE_DIR: {BASE_DIR}")
logger.debug(f"ROOT_DIR: {ROOT_DIR}")
logger.debug(f"CONFIG_PATH: {CONFIG_PATH}")


def get_collections_folder() -> Path:
    """Return the main collection folder for all wallpapers"""
    logger.debug("Getting collections folder path")
    home = Path.home()
    collection_dir = home / "Pictures" / "Tapeciarnia"
    
    logger.debug(f"Home directory: {home}")
    logger.debug(f"Collection directory: {collection_dir}")
    
    try:
        collection_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Collections folder ensured: {collection_dir}")
        return collection_dir
    except Exception as e:
        logger.error(f"Failed to create collections folder: {e}", exc_info=True)
        raise


logger.debug("Creating collection directory structure")
COLLECTION_DIR = get_collections_folder()
VIDEOS_DIR = COLLECTION_DIR / "Videos"
IMAGES_DIR = COLLECTION_DIR / "Images" 
FAVS_DIR = COLLECTION_DIR / "Favorites"

logger.debug(f"COLLECTION_DIR: {COLLECTION_DIR}")
logger.debug(f"VIDEOS_DIR: {VIDEOS_DIR}")
logger.debug(f"IMAGES_DIR: {IMAGES_DIR}")
logger.debug(f"FAVS_DIR: {FAVS_DIR}")


# Ensure folders exist
logger.info("Ensuring collection directories exist")
for d in (COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR):
    try:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {d}")
    except Exception as e:
        logger.error(f"Failed to create directory {d}: {e}", exc_info=True)
        raise

TMP_DOWNLOAD_FILE = COLLECTION_DIR / "download_path.tmp"
TRANSLATIONS_DIR = BASE_DIR / "code" / "scripts" / "translations"

logger.debug(f"TMP_DOWNLOAD_FILE: {TMP_DOWNLOAD_FILE}")
logger.debug(f"TRANSLATIONS_DIR: {TRANSLATIONS_DIR}")


# Config file init
logger.debug("Initializing config file")
if not CONFIG_PATH.exists():
    logger.info(f"Config file does not exist, creating: {CONFIG_PATH}")
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps({}), encoding="utf-8")
        logger.info("Config file created successfully")
    except Exception as e:
        logger.error(f"Failed to create config file: {e}", exc_info=True)
        raise
else:
    logger.debug("Config file already exists")


# Executable paths
def get_mpv_path() -> Path:
    """Get MPV executable path"""
    logger.debug("Searching for MPV executable")
    candidates = [
        BASE_DIR / "bin" / "mpv" / "mpv.exe",
        BASE_DIR / "bin" / "tools" / "mpv.exe",
        BASE_DIR / "bin" / "mpv.exe",
    ]
    
    logger.debug(f"MPV candidate paths: {candidates}")
    
    for c in candidates:
        if c.exists():
            logger.info(f"MPV found at: {c}")
            return c
        else:
            logger.debug(f"MPV not found at: {c}")
    
    logger.warning("MPV executable not found in any candidate locations")
    return None


def get_weepe_path() -> Path:
    """Get Weepe executable path for Windows wallpaper"""
    logger.debug("Searching for Weepe executable")
    candidates = [
        BASE_DIR / "bin" / "weepe" / "weepe.exe",
        BASE_DIR / "bin" / "tools" / "weepe.exe",
        BASE_DIR / "bin" / "weepe.exe",
    ]
    
    logger.debug(f"Weepe candidate paths: {candidates}")
    
    for c in candidates:
        if c.exists():
            logger.info(f"Weepe found at: {c}")
            return c
        else:
            logger.debug(f"Weepe not found at: {c}")
    
    logger.warning("Weepe executable not found in any candidate locations")
    return None


def get_style_path() -> Path:
    """Get style file path"""
    logger.debug("Getting style file path")
    style_path = BASE_DIR / "ui" / "style" / "style.qss"
    
    if style_path.exists():
        logger.debug(f"Style file exists: {style_path}")
    else:
        logger.warning(f"Style file does not exist: {style_path}")
    
    return style_path


def verify_directory_structure() -> bool:
    """
    Verify that all required directories exist and are accessible
    
    Returns:
        bool: True if all directories are accessible, False otherwise
    """
    logger.info("Verifying directory structure")
    required_dirs = [COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
    problems = []
    
    for directory in required_dirs:
        try:
            if not directory.exists():
                problems.append(f"Directory does not exist: {directory}")
                logger.error(f"Missing directory: {directory}")
            elif not os.access(directory, os.W_OK):
                problems.append(f"Directory not writable: {directory}")
                logger.error(f"Directory not writable: {directory}")
            else:
                logger.debug(f"Directory verified: {directory}")
        except Exception as e:
            problems.append(f"Error accessing {directory}: {e}")
            logger.error(f"Error accessing directory {directory}: {e}")
    
    if problems:
        logger.error(f"Directory structure verification failed: {problems}")
        return False
    
    logger.info("Directory structure verified successfully")
    return True


def get_available_executables() -> dict:
    """
    Get information about available executables for debugging
    
    Returns:
        dict: Information about found executables
    """
    logger.debug("Checking available executables")
    executables = {
        'mpv': get_mpv_path(),
        'weepe': get_weepe_path(),
        'style_file': get_style_path()
    }
    
    # Log availability
    for name, path in executables.items():
        if path and path.exists():
            logger.debug(f"Executable available - {name}: {path}")
        else:
            logger.debug(f"Executable not available - {name}: {path}")
    
    return executables


def get_directory_sizes() -> dict:
    """
    Get size information for collection directories
    
    Returns:
        dict: Size information for each directory
    """
    logger.debug("Calculating directory sizes")
    sizes = {}
    
    for directory in [COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]:
        try:
            total_size = 0
            file_count = 0
            
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            sizes[str(directory)] = {
                'size_bytes': total_size,
                'size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count
            }
            
            logger.debug(f"Directory size - {directory}: {file_count} files, {total_size} bytes")
            
        except Exception as e:
            logger.error(f"Error calculating size for {directory}: {e}")
            sizes[str(directory)] = {'error': str(e)}
    
    return sizes


# Backward compatibility
get_app_root = get_app_root
get_weepe_path = get_weepe_path
get_mpv_path = get_mpv_path
get_style_path = get_style_path

# Log initialization completion
logger.info("Path utilities initialization completed")
logger.debug(f"Platform: {platform.system()}")
logger.debug(f"Python version: {sys.version}")