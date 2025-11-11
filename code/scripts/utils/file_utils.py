import shutil
import requests
import re
import logging
from pathlib import Path
from typing import Optional

from .path_utils import IMAGES_DIR, TMP_DOWNLOAD_FILE

# Get logger for this module
logger = logging.getLogger(__name__)


def download_image(url: str) -> str:
    """Download image from URL and return local path"""
    logger.info(f"Starting image download from: {url}")
    
    try:
        logger.debug("Making HTTP GET request with streaming")
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        logger.debug(f"HTTP request successful - status: {r.status_code}, content-type: {r.headers.get('content-type', 'unknown')}")
        
        # Determine file extension
        ext = Path(url).suffix 
        if not ext or ext.lower() not in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
            ext = '.jpg'
            logger.debug(f"No valid extension in URL, defaulting to: {ext}")
        else:
            logger.debug(f"Using extension from URL: {ext}")
        
        # Create safe filename
        original_stem = Path(url).stem
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", original_stem)[:60]
        dest = IMAGES_DIR / f"{safe}{ext}"
        logger.debug(f"Original filename: {original_stem}, Safe filename: {safe}{ext}")
        
        # Ensure directory exists
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {IMAGES_DIR}")
        
        # Download and save file
        file_size = 0
        chunk_count = 0
        logger.info(f"Downloading image to: {dest}")
        
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
                    file_size += len(chunk)
                    chunk_count += 1
                    
                    # Log progress for large files
                    if chunk_count % 100 == 0:  # Log every ~800KB
                        logger.debug(f"Download progress: {file_size} bytes received, {chunk_count} chunks")
        
        logger.info(f"Image download completed - File: {dest.name}, Size: {file_size} bytes, Chunks: {chunk_count}")
        return str(dest)
        
    except requests.exceptions.Timeout:
        logger.error(f"Image download timed out: {url}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error downloading image: {e} - URL: {url}")
        logger.error(f"HTTP status: {e.response.status_code if e.response else 'unknown'}")
        raise
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error downloading image: {url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception downloading image: {e} - URL: {url}")
        raise
    except IOError as e:
        logger.error(f"File I/O error saving downloaded image: {e} - Destination: {dest}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading image: {e} - URL: {url}", exc_info=True)
        raise


def copy_to_collection(file_path: Path, dest_folder: Path) -> Path:
    """Copy file to collection folder and return destination path"""
    logger.info(f"Copying file to collection - Source: {file_path}, Destination: {dest_folder}")
    
    if not file_path.exists():
        logger.error(f"Source file does not exist: {file_path}")
        raise FileNotFoundError(f"Source file not found: {file_path}")
    
    try:
        # Get file info before copy
        file_size = file_path.stat().st_size
        logger.debug(f"Source file info - Size: {file_size} bytes, Exists: {file_path.exists()}")
        
        # Ensure destination directory exists
        dest_folder.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured destination directory exists: {dest_folder}")
        
        dest = dest_folder / file_path.name
        logger.debug(f"Destination path: {dest}")
        
        if dest.exists():
            dest_size = dest.stat().st_size
            logger.warning(f"Destination file already exists - Path: {dest}, Size: {dest_size} bytes")
            logger.info("Skipping copy as file already exists in collection")
        else:
            logger.debug("Starting file copy operation")
            shutil.copy2(file_path, dest)  # copy2 preserves metadata
            
            # Verify copy was successful
            if dest.exists():
                copied_size = dest.stat().st_size
                logger.info(f"File copied successfully - Source: {file_path.name}, Destination: {dest}, Size: {copied_size} bytes")
                
                if copied_size != file_size:
                    logger.warning(f"File size mismatch after copy - Source: {file_size} bytes, Copied: {copied_size} bytes")
            else:
                logger.error(f"Copy operation failed - destination file not created: {dest}")
                raise IOError(f"Failed to copy file to {dest}")
        
        return dest
        
    except PermissionError as e:
        logger.error(f"Permission error copying file: {e} - Source: {file_path}, Dest: {dest_folder}")
        raise
    except shutil.SameFileError:
        logger.warning(f"Source and destination are the same file: {file_path}")
        return file_path
    except OSError as e:
        logger.error(f"OS error copying file: {e} - Source: {file_path}, Dest: {dest_folder}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error copying file: {e} - Source: {file_path}, Dest: {dest_folder}", exc_info=True)
        raise


def cleanup_temp_marker():
    """Remove temporary download marker"""
    logger.debug("Cleaning up temporary download marker")
    
    if TMP_DOWNLOAD_FILE.exists():
        try:
            file_size = TMP_DOWNLOAD_FILE.stat().st_size
            logger.debug(f"Temporary marker exists - Path: {TMP_DOWNLOAD_FILE}, Size: {file_size} bytes")
            
            TMP_DOWNLOAD_FILE.unlink()
            logger.info("Temporary download marker removed successfully")
            
        except PermissionError as e:
            logger.error(f"Permission error removing temporary marker: {e} - File: {TMP_DOWNLOAD_FILE}")
        except FileNotFoundError:
            logger.debug("Temporary marker already removed by another process")
        except Exception as e:
            logger.error(f"Unexpected error removing temporary marker: {e} - File: {TMP_DOWNLOAD_FILE}", exc_info=True)
    else:
        logger.debug("No temporary download marker found to clean up")


def safe_delete_file(file_path: Path) -> bool:
    """
    Safely delete a file with comprehensive logging
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    logger.info(f"Attempting to safely delete file: {file_path}")
    
    if not file_path.exists():
        logger.warning(f"File does not exist, nothing to delete: {file_path}")
        return True
    
    try:
        file_size = file_path.stat().st_size
        logger.debug(f"File info - Size: {file_size} bytes, Path: {file_path}")
        
        file_path.unlink()
        
        # Verify deletion
        if not file_path.exists():
            logger.info(f"File deleted successfully: {file_path}")
            return True
        else:
            logger.error(f"File deletion failed - file still exists: {file_path}")
            return False
            
    except PermissionError as e:
        logger.error(f"Permission error deleting file: {e} - File: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting file: {e} - File: {file_path}", exc_info=True)
        return False


def get_file_info(file_path: Path) -> Optional[dict]:
    """
    Get detailed information about a file for debugging
    
    Args:
        file_path: Path to the file
        
    Returns:
        dict: File information or None if file doesn't exist
    """
    logger.debug(f"Getting file info: {file_path}")
    
    if not file_path.exists():
        logger.debug(f"File does not exist: {file_path}")
        return None
    
    try:
        stat = file_path.stat()
        info = {
            'path': str(file_path),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'extension': file_path.suffix.lower(),
            'exists': True
        }
        logger.debug(f"File info retrieved: {info}")
        return info
    except Exception as e:
        logger.error(f"Error getting file info: {e} - File: {file_path}")
        return None