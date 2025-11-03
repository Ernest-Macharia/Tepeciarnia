import shutil
import requests
import re
from pathlib import Path

from .path_utils import IMAGES_DIR, TMP_DOWNLOAD_FILE

def download_image(url: str) -> str:
    """Download image from URL and return local path"""
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    
    ext = Path(url).suffix 
    if not ext or ext.lower() not in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
        ext = '.jpg'
        
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(url).stem)[:60]
    dest = IMAGES_DIR / f"{safe}{ext}"
    
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(dest, "wb") as fh:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)
    
    return str(dest)

def copy_to_collection(file_path: Path, dest_folder: Path) -> Path:
    """Copy file to collection folder and return destination path"""
    dest = dest_folder / file_path.name
    if not dest.exists():
        shutil.copy2(file_path, dest)
    return dest

def cleanup_temp_marker():
    """Remove temporary download marker"""
    if TMP_DOWNLOAD_FILE.exists():
        try:
            TMP_DOWNLOAD_FILE.unlink()
        except Exception:
            pass