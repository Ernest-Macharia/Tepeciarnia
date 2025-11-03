import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

from utils.system_utils import which, set_static_desktop_wallpaper
from utils.path_utils import BASE_DIR


class WallpaperController:
    def __init__(self):
        self.player_procs = []
        self.current_is_video = False

    def stop(self):
        """Stop all wallpaper processes"""
        if sys.platform.startswith("linux"):
            subprocess.call("pkill -f xwinwrap", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("pkill -f mpv", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            subprocess.call("taskkill /F /IM weepe.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM mpv.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM ffplay.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for p in list(self.player_procs):
            try:
                p.terminate()
            except Exception:
                pass
        self.player_procs = []
        self.current_is_video = False

    def _get_weepe_path(self) -> Optional[Path]:
        """Get Weepe executable path for Windows"""
        candidates = [
            BASE_DIR / "bin" / "tools" / "weepe.exe",
            BASE_DIR / "bin" / "tools" / "weepe",
            BASE_DIR / "bin" / "weepe.exe",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def start_video(self, video_path_or_url: str):
        """Starts a video as wallpaper using platform-specific tools."""
        self.stop()
        self.current_is_video = True
        
        # If remote URL and mpv available -> try streaming first
        if str(video_path_or_url).lower().startswith("http"):
            mpv = which("mpv")
            if mpv:
                try:
                    p = subprocess.Popen([mpv, "--loop", "--no-audio", "--no-osd-bar", "--fullscreen", "--no-border", video_path_or_url],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception as e:
                    logging.error(f"DEBUG: Streaming failed: {e}")
        
        # Windows: Use Weepe (proper wallpaper)
        if sys.platform.startswith("win"):
            weepe_path = self._get_weepe_path()
            if weepe_path:
                try:
                    cmd = f'"{weepe_path}" "{video_path_or_url}"'
                    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception as e:
                    logging.error(f"DEBUG: Weepe failed: {e}")
            
            # Fallback: Try mpv if available
            mpv = which("mpv")
            if mpv:
                try:
                    p = subprocess.Popen([mpv, "--loop", "--no-audio", "--fullscreen", "--no-border", str(video_path_or_url)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception as e:
                    logging.error(f"DEBUG: mpv fallback failed: {e}")
            
            # Final fallback: ffplay
            ffplay = which("ffplay")
            if ffplay:
                try:
                    cmd = f'start "" /min "{ffplay}" -autoexit -loop 0 -an -fs "{video_path_or_url}"'
                    subprocess.Popen(cmd, shell=True)
                    return
                except Exception as e:
                    logging.error(f"DEBUG: ffplay fallback failed: {e}")
                    
            raise RuntimeError("No suitable video wallpaper player found on Windows.")
        
        # Linux: Use xwinwrap + mpv (proper wallpaper)
        elif sys.platform.startswith("linux"):
            xw = which("xwinwrap")
            mpv = which("mpv")
            if xw and mpv:
                try:
                    cmd = f"{xw} -ov -fs -- {mpv} --loop --no-audio --no-osd-bar --wid=WID '{video_path_or_url}'"
                    p = subprocess.Popen(cmd, shell=True, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception as e:
                    logging.error(f"DEBUG: xwinwrap failed: {e}")
            
            # Fallback: mpv fullscreen
            if mpv:
                try:
                    p = subprocess.Popen([mpv, "--loop", "--no-audio", "--no-osd-bar", "--fullscreen", "--no-border", str(video_path_or_url)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception as e:
                    logging.error(f"DEBUG: mpv fullscreen failed: {e}")
            raise RuntimeError("No mpv (or suitable player) found on Linux.")
        
        else:
            # macOS or other - use basic fullscreen
            mpv = which("mpv")
            if mpv:
                p = subprocess.Popen([mpv, "--loop", "--no-audio", "--fullscreen", "--no-border", str(video_path_or_url)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                return
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

    def start_image(self, image_path: str):
        """Set static wallpaper"""
        self.stop()
        self.current_is_video = False
        try:
            set_static_desktop_wallpaper(image_path)
        except Exception as e:
            logging.error(f"DEBUG: Failed to set static wallpaper: {e}")