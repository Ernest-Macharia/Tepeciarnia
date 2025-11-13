import re
from pathlib import Path
from typing import Optional

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

def get_media_type(s: str) -> str:
    """Determine media type (image, video, or unknown)"""
    if is_image_url_or_path(s):
        return "image"
    elif is_video_url_or_path(s):
        return "video"
    else:
        return "unknown"