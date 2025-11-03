import re
from pathlib import Path
from typing import Optional

def is_image_url_or_path(s: str) -> bool:
    s = s.lower()
    return bool(re.search(r"\.(jpe?g|png|bmp|gif)$", s)) or (s.startswith("http") and bool(re.search(r"\.(jpe?g|png|bmp|gif)(\?.*)?$", s)))

def is_video_url_or_path(s: str) -> bool:
    s = s.lower()
    return bool(re.search(r"\.(mp4|mkv|webm|avi|mov)$", s)) or (s.startswith("http") and bool(re.search(r"\.(mp4|mkv|webm|avi|mov)(\?.*)?$", s)))

def validate_url_or_path(s: str) -> Optional[str]:
    s = (s or "").strip()
    if not s:
        return None
    # Local file?
    p = Path(s)
    if p.exists():
        return str(p)
    # http/https
    if s.lower().startswith(("http://", "https://")):
        return s
    # tapeciarnia scheme
    if s.lower().startswith("tapeciarnia:"):
        m = re.match(r"tapeciarnia:\[?(.*)\]?$", s, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

def validate_cli_arg(arg: str) -> Optional[str]:
    parsed = validate_url_or_path(arg)
    if parsed:
        return parsed
    if arg.lower().startswith("tapeciarnia:"):
        m = re.match(r"tapeciarnia:\[?(.*)\]?$", arg, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None