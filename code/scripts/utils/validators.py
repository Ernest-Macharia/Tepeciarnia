import re
import logging
from pathlib import Path
from typing import Optional

from code.scripts.utils.path_utils import VIDEOS_DIR, IMAGES_DIR, FAVS_DIR

def is_image_url_or_path(s: str) -> bool:
    """Check if string is an image URL or path - IMPROVED"""
    s = s.lower()
    
    # Check for image file extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
    
    # Check local file path
    if any(s.endswith(ext) for ext in image_extensions):
        return True
    
    # Check HTTP URL with image extension
    if s.startswith("http"):
        # More flexible pattern to handle query parameters and URL fragments
        pattern = r"\.(jpe?g|png|bmp|gif|webp)(\?.*)?$"
        return bool(re.search(pattern, s))
    
    return False

def is_video_url_or_path(s: str) -> bool:
    """Check if string is a video URL or path - IMPROVED"""
    s = s.lower()
    
    # Check for video file extensions
    video_extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv')
    
    # Check local file path
    if any(s.endswith(ext) for ext in video_extensions):
        return True
    
    # Check HTTP URL with video extension
    if s.startswith("http"):
        # More flexible pattern to handle query parameters and URL fragments
        pattern = r"\.(mp4|mkv|webm|avi|mov|flv|wmv)(\?.*)?$"
        if bool(re.search(pattern, s)):
            return True
        
        # Also check for video hosting platforms
        video_hosts = [
            "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
            "twitch.tv", "instagram.com", "tiktok.com", "facebook.com/watch"
        ]
        return any(host in s for host in video_hosts)
    
    return False

def validate_url_or_path(s: str) -> Optional[str]:
    """Validate and normalize URL or path - IMPROVED"""
    s = (s or "").strip()
    if not s:
        return None
    
    # Local file?
    p = Path(s)
    if p.exists():
        return str(p.resolve())
    
    # http/https URL
    if s.lower().startswith(("http://", "https://")):
        return s
    
    # tapeciarnia scheme
    if s.lower().startswith("tapeciarnia:"):
        m = re.match(r"tapeciarnia:\[?(.*)\]?$", s, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    return None

def validate_cli_arg(arg: str) -> Optional[str]:
    """Validate CLI argument - IMPROVED"""
    parsed = validate_url_or_path(arg)
    if parsed:
        return parsed
    
    if arg.lower().startswith("tapeciarnia:"):
        m = re.match(r"tapeciarnia:\[?(.*)\]?$", arg, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    return None

def _get_media_files(self, media_type="all"):
    """Get media files from ALL sources (My Collection + Favorites)"""
    logging.debug(f"Getting media files - type: {media_type}, range: {self.current_range}")
    files = []
    
    # ALWAYS search both My Collection AND Favorites folders for shuffle
    search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
    source_type = "all sources (collection + favorites)"
    
    logging.debug(f"Using ALL sources for shuffle: {[str(f) for f in search_folders]}")
    
    # Define extensions based on media type
    if media_type == "mp4":
        extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
    elif media_type == "wallpaper":
        extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    else:
        extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.mkv', '.webm', '.avi', '.mov')
    
    for folder in search_folders:
        if folder.exists():
            folder_files = [
                f for f in folder.iterdir() 
                if f.is_file() and f.suffix.lower() in extensions
            ]
            files.extend(folder_files)
            logging.debug(f"Found {len(folder_files)} files in {folder}")
    
    logging.debug(f"Total media files found from {source_type}: {len(files)}")
    return files