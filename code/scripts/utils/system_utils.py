import sys
import subprocess
import locale
import shutil
import ctypes
from pathlib import Path
from typing import Optional

def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def current_system_locale() -> str:
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            return loc.split("_")[0]
    except Exception:
        pass
    return "en"

def get_current_desktop_wallpaper() -> Optional[str]:
    if sys.platform.startswith("win"):
        try:
            buf = ctypes.create_unicode_buffer(260)
            SPI_GETDESKWALLPAPER = 0x0073
            ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buf, 0)
            return buf.value or None
        except Exception:
            return None
    elif sys.platform.startswith("linux"):
        try:
            res = subprocess.run(["gsettings", "get", "org.gnome.desktop.background", "picture-uri"],
                                  capture_output=True, text=True)
            if res.returncode == 0:
                val = res.stdout.strip().strip("'\"")
                if val.startswith("file://"):
                    return val[7:]
                return val
        except Exception:
            pass
        return None
    else:
        return None

def set_static_desktop_wallpaper(path: str) -> bool:
    try:
        if sys.platform.startswith("win"):
            import ctypes
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, str(path), 3)
            return True
        elif sys.platform.startswith("linux"):
            uri = f"file://{str(path)}"
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri], check=False)
            return True
    except Exception:
        return False
    return False