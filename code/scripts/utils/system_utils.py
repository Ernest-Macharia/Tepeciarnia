import sys
import subprocess
import locale
import shutil
import ctypes
import logging
from pathlib import Path
from typing import Optional

# Get logger for this module
logger = logging.getLogger(__name__)


def which(cmd: str) -> Optional[str]:
    """Find executable in system PATH with logging"""
    logger.debug(f"Searching for executable in PATH: {cmd}")
    
    try:
        result = shutil.which(cmd)
        if result:
            logger.debug(f"Executable found: {result}")
        else:
            logger.debug(f"Executable not found in PATH: {cmd}")
        return result
    except Exception as e:
        logger.error(f"Error searching for executable '{cmd}': {e}")
        return None


def current_system_locale() -> str:
    """Get current system locale with logging"""
    logger.debug("Detecting system locale")
    
    try:
        loc = locale.getdefaultlocale()[0]
        logger.debug(f"Raw locale detected: {loc}")
        
        if loc:
            language_code = loc.split("_")[0]
            logger.info(f"System locale determined: {language_code}")
            return language_code
        else:
            logger.warning("No locale detected, defaulting to 'en'")
            return "en"
            
    except Exception as e:
        logger.error(f"Error detecting system locale: {e}", exc_info=True)
        logger.warning("Defaulting to 'en' due to locale detection error")
        return "en"


def get_current_desktop_wallpaper() -> Optional[str]:
    """Get current desktop wallpaper path with comprehensive logging"""
    logger.debug("Retrieving current desktop wallpaper")
    
    if sys.platform.startswith("win"):
        logger.debug("Windows platform detected for wallpaper retrieval")
        try:
            buf = ctypes.create_unicode_buffer(260)
            SPI_GETDESKWALLPAPER = 0x0073
            logger.debug("Calling SystemParametersInfoW for wallpaper")
            
            result = ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buf, 0)
            
            if result and buf.value:
                wallpaper_path = buf.value
                logger.info(f"Current Windows wallpaper: {wallpaper_path}")
                return wallpaper_path
            else:
                logger.warning("SystemParametersInfoW failed or returned empty wallpaper path")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving Windows wallpaper: {e}", exc_info=True)
            return None
            
    elif sys.platform.startswith("linux"):
        logger.debug("Linux platform detected for wallpaper retrieval")
        try:
            logger.debug("Attempting to get wallpaper via gsettings")
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.background", "picture-uri"],
                capture_output=True, 
                text=True,
                timeout=10  # Add timeout to prevent hanging
            )
            
            if res.returncode == 0:
                val = res.stdout.strip().strip("'\"")
                logger.debug(f"Raw gsettings output: {val}")
                
                if val.startswith("file://"):
                    wallpaper_path = val[7:]
                    logger.info(f"Current Linux wallpaper: {wallpaper_path}")
                    return wallpaper_path
                elif val:
                    logger.info(f"Current Linux wallpaper (non-file URI): {val}")
                    return val
                else:
                    logger.warning("gsettings returned empty wallpaper URI")
                    return None
            else:
                logger.error(f"gsettings command failed - returncode: {res.returncode}, stderr: {res.stderr.strip()}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("gsettings command timed out while retrieving wallpaper")
            return None
        except FileNotFoundError:
            logger.error("gsettings command not found - likely not running on GNOME desktop")
            return None
        except Exception as e:
            logger.error(f"Error retrieving Linux wallpaper: {e}", exc_info=True)
            return None
    else:
        logger.warning(f"Unsupported platform for wallpaper retrieval: {sys.platform}")
        return None


def set_static_desktop_wallpaper(path: str) -> bool:
    """Set static desktop wallpaper with comprehensive logging"""
    logger.info(f"Setting static desktop wallpaper: {path}")
    
    # Validate path exists
    wallpaper_path = Path(path)
    if not wallpaper_path.exists():
        logger.error(f"Wallpaper file does not exist: {path}")
        return False
    
    try:
        if sys.platform.startswith("win"):
            logger.debug("Windows platform detected for wallpaper setting")
            try:
                import ctypes
                SPI_SETDESKWALLPAPER = 20
                logger.debug("Calling SystemParametersInfoW to set wallpaper")
                
                # Convert to absolute path for Windows API
                absolute_path = str(wallpaper_path.resolve())
                logger.debug(f"Using absolute path for Windows: {absolute_path}")
                
                result = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, absolute_path, 3)
                
                if result:
                    logger.info(f"Windows wallpaper set successfully: {absolute_path}")
                    return True
                else:
                    logger.error("SystemParametersInfoW failed to set wallpaper")
                    # Get last error for more details
                    last_error = ctypes.windll.kernel32.GetLastError()
                    logger.error(f"Windows API last error: {last_error}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error setting Windows wallpaper: {e}", exc_info=True)
                return False
                
        elif sys.platform.startswith("linux"):
            logger.debug("Linux platform detected for wallpaper setting")
            try:
                uri = f"file://{str(wallpaper_path.resolve())}"
                logger.debug(f"Using URI for gsettings: {uri}")
                
                result = subprocess.run(
                    ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info(f"Linux wallpaper set successfully via gsettings: {uri}")
                    return True
                else:
                    logger.error(f"gsettings failed to set wallpaper - returncode: {result.returncode}")
                    logger.error(f"gsettings stderr: {result.stderr.strip()}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error("gsettings command timed out while setting wallpaper")
                return False
            except FileNotFoundError:
                logger.error("gsettings command not found - cannot set wallpaper on this Linux system")
                return False
            except Exception as e:
                logger.error(f"Error setting Linux wallpaper: {e}", exc_info=True)
                return False
        else:
            logger.warning(f"Unsupported platform for wallpaper setting: {sys.platform}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error setting wallpaper: {e}", exc_info=True)
        return False


def get_system_info() -> dict:
    """
    Get comprehensive system information for debugging
    
    Returns:
        dict: System information including platform, desktop environment, etc.
    """
    logger.debug("Collecting system information")
    system_info = {
        'platform': sys.platform,
        'python_version': sys.version,
        'executable': sys.executable,
    }
    
    try:
        # Platform-specific information
        if sys.platform.startswith("win"):
            system_info['windows_version'] = f"{sys.getwindowsversion().major}.{sys.getwindowsversion().minor}"
        elif sys.platform.startswith("linux"):
            # Try to detect desktop environment
            de = os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')
            system_info['desktop_environment'] = de
            system_info['current_wallpaper'] = get_current_desktop_wallpaper()
            
        logger.debug(f"System information collected: {system_info}")
        
    except Exception as e:
        logger.error(f"Error collecting system information: {e}")
        system_info['error'] = str(e)
    
    return system_info


def verify_wallpaper_access() -> bool:
    """
    Verify that wallpaper operations can be performed on this system
    
    Returns:
        bool: True if wallpaper operations are supported, False otherwise
    """
    logger.debug("Verifying wallpaper access capabilities")
    
    if sys.platform.startswith("win"):
        logger.debug("Windows platform supports wallpaper operations")
        return True
    elif sys.platform.startswith("linux"):
        # Check if gsettings is available
        try:
            result = subprocess.run(["which", "gsettings"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.debug("Linux system supports wallpaper operations via gsettings")
                return True
            else:
                logger.warning("Linux system does not have gsettings - wallpaper operations may not work")
                return False
        except Exception as e:
            logger.error(f"Error verifying Linux wallpaper access: {e}")
            return False
    else:
        logger.warning(f"Wallpaper operations not supported on platform: {sys.platform}")
        return False


# Import os for system_info function
import os

# Log module initialization
logger.debug("System utilities module initialized")